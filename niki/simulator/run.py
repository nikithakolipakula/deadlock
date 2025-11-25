"""
CLI Runner for Deadlock Simulator

Command-line interface for running simulations.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from .scenario import ScenarioLoader, create_simple_scenario
from .dispatcher import EventDispatcher, SimulationMode
from engine.rag import analyze_deadlock


@click.command()
@click.option(
    "--scenario",
    "-s",
    type=click.Path(exists=True),
    help="Path to scenario file (JSON or YAML)"
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["continuous", "step", "realtime"]),
    default="continuous",
    help="Simulation mode"
)
@click.option(
    "--speed",
    type=float,
    default=1.0,
    help="Speed multiplier for realtime mode"
)
@click.option(
    "--policy",
    "-p",
    type=click.Choice(["none", "bankers", "resource_ordering", "conservative"]),
    default=None,
    help="Override prevention policy"
)
@click.option(
    "--recovery",
    "-r",
    type=click.Choice(["none", "preempt_low_priority", "preempt_min_cost", "kill_one", "kill_all"]),
    default=None,
    help="Override recovery policy"
)
@click.option(
    "--step",
    "step_mode",
    is_flag=True,
    help="Enable step-by-step execution (same as --mode step)"
)
@click.option(
    "--export",
    "-e",
    type=click.Path(),
    help="Export snapshots to JSON file"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output"
)
@click.option(
    "--simple",
    is_flag=True,
    help="Run a simple generated scenario instead of loading from file"
)
def main(
    scenario: Optional[str],
    mode: str,
    speed: float,
    policy: Optional[str],
    recovery: Optional[str],
    step_mode: bool,
    export: Optional[str],
    verbose: bool,
    simple: bool
) -> None:
    """
    Deadlock Detection and Recovery Simulator
    
    Run deadlock scenarios with configurable prevention and recovery policies.
    
    Examples:
    
        # Run a scenario file
        python -m simulator.run --scenario examples/simple_deadlock.json
        
        # Step through scenario with Banker's algorithm
        python -m simulator.run -s examples/banker_safe.json --step --policy bankers
        
        # Run with recovery policy
        python -m simulator.run -s examples/dining_philosophers.json -r preempt_low_priority
        
        # Generate and run simple scenario
        python -m simulator.run --simple --verbose
    """
    click.echo("🔒 Deadlock Detection & Recovery Simulator\n")
    
    # Load or generate scenario
    if simple:
        click.echo("Generating simple deadlock scenario...")
        scen = create_simple_scenario(num_processes=3, num_resources=3)
    elif scenario:
        click.echo(f"Loading scenario: {scenario}")
        try:
            scen = ScenarioLoader.load_from_file(scenario)
        except Exception as e:
            click.echo(f"❌ Error loading scenario: {e}", err=True)
            sys.exit(1)
    else:
        click.echo("❌ Please specify --scenario or use --simple", err=True)
        sys.exit(1)
    
    # Override policies if specified
    if policy:
        scen.prevention_policy = policy
    if recovery:
        scen.recovery_policy = recovery
    
    # Determine mode
    if step_mode:
        mode = "step"
    sim_mode = SimulationMode(mode)
    
    # Print scenario info
    click.echo(f"\n📋 Scenario: {scen.name}")
    if scen.description:
        click.echo(f"   {scen.description}")
    click.echo(f"\n   Resources: {len(scen.resources)}")
    click.echo(f"   Processes: {len(scen.processes)}")
    click.echo(f"   Events: {len(scen.events)}")
    click.echo(f"   Prevention Policy: {scen.prevention_policy}")
    click.echo(f"   Recovery Policy: {scen.recovery_policy}")
    click.echo()
    
    # Create dispatcher
    dispatcher = EventDispatcher(scen, mode=sim_mode, speed=speed)
    
    # Add callbacks for verbose output
    if verbose:
        def on_event(event, result):
            icon = "✓" if result["success"] else "✗"
            click.echo(f"  [{event.time:.1f}s] {icon} {result['message']}")
        
        def on_deadlock(analysis):
            click.echo(f"\n  ⚠️  DEADLOCK DETECTED!")
            click.echo(f"     Processes: {', '.join(analysis['deadlocked_processes'])}")
            click.echo(f"     Resources: {', '.join(analysis['deadlocked_resources'])}")
        
        def on_prevention(event, allowed, reason):
            if not allowed:
                click.echo(f"  🛡️  Prevention: {reason}")
        
        def on_recovery(result):
            if result["success"]:
                click.echo(f"  🔧 Recovery: {result['reason']}")
                click.echo(f"     Affected: {', '.join(result['affected_processes'])}")
            else:
                click.echo(f"  ❌ Recovery failed: {result['reason']}")
        
        dispatcher.add_callback("event", on_event)
        dispatcher.add_callback("deadlock", on_deadlock)
        dispatcher.add_callback("prevention", on_prevention)
        dispatcher.add_callback("recovery", on_recovery)
    
    # Run simulation
    click.echo("▶️  Starting simulation...\n")
    
    if sim_mode == SimulationMode.STEP:
        # Step-by-step execution
        event_num = 1
        while True:
            click.echo(f"Step {event_num}/{len(scen.events)}")
            result = dispatcher.step()
            
            if result is None:
                click.echo("\n✓ Simulation complete")
                break
            
            if verbose:
                pass  # Already printed by callbacks
            else:
                icon = "✓" if result["success"] else "✗"
                click.echo(f"  {icon} {result['message']}")
            
            event_num += 1
            
            if event_num <= len(scen.events):
                click.echo()
                click.pause("Press any key for next step...")
                click.echo()
    else:
        # Continuous execution
        snapshots = dispatcher.run()
        click.echo(f"\n✓ Simulation complete ({len(snapshots)} snapshots)\n")
    
    # Print summary
    summary = dispatcher.get_summary()
    click.echo("📊 Summary:")
    click.echo(f"   Total Events: {summary['total_events']}")
    click.echo(f"   Executed: {summary['executed_events']}")
    click.echo(f"   Deadlocks Detected: {summary['deadlock_detected_count']}")
    click.echo(f"   Recovery Attempts: {summary['recovery_attempts']}")
    
    # Final deadlock analysis
    final_analysis = analyze_deadlock(dispatcher.state)
    if final_analysis["has_deadlock"]:
        click.echo(f"\n⚠️  Final State: DEADLOCKED")
        click.echo(f"   Deadlocked Processes: {', '.join(final_analysis['deadlocked_processes'])}")
    else:
        click.echo(f"\n✓ Final State: NO DEADLOCK")
    
    # Export if requested
    if export:
        import json
        export_path = Path(export)
        export_data = {
            "scenario": scen.model_dump(),
            "summary": summary,
            "snapshots": [
                {
                    "time": s.time,
                    "event_index": s.event_index,
                    "system_state": s.system_state,
                    "deadlock_analysis": s.deadlock_analysis,
                    "last_event": s.last_event,
                    "recovery_result": s.recovery_result
                }
                for s in dispatcher.snapshots
            ]
        }
        export_path.write_text(json.dumps(export_data, indent=2))
        click.echo(f"\n💾 Exported to: {export}")


if __name__ == "__main__":
    main()
