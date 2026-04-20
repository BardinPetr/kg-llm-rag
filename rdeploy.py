#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from ray import serve


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def format_replica_states(replica_states):
    if not replica_states:
        return ""
    parts = [f"{count} {state}" for state, count in replica_states.items()]
    return f" ({', '.join(parts)})"


def print_status(serve_status):
    clear_screen()
    print("\n")
    for app_name, app_status in serve_status.applications.items():
        print(f"[{app_status.status.value}] {app_name}:")

        for dep_name, dep_status in app_status.deployments.items():
            replica_info = format_replica_states(dep_status.replica_states)
            print(f"  [{dep_status.status.value}] {dep_name}: {replica_info}")
            if dep_status.message:
                print(f"    └─ {dep_status.message.replace("\n", ";; ")}")


def check_deployment_complete(serve_status):
    from ray.serve.schema import ApplicationStatus, DeploymentStatus

    all_running = True
    any_failed = False

    for app_status in serve_status.applications.values():
        if app_status.status == ApplicationStatus.DEPLOY_FAILED:
            any_failed = True
        elif app_status.status != ApplicationStatus.RUNNING:
            all_running = False

        for dep_status in app_status.deployments.values():
            if dep_status.status == DeploymentStatus.DEPLOY_FAILED:
                any_failed = True
            elif dep_status.status != DeploymentStatus.HEALTHY:
                all_running = False

    return all_running, any_failed


def main():
    if len(sys.argv) < 2:
        print("Usage: deploy.py <config.yaml>")
        sys.exit(1)

    config_path = sys.argv[1]

    print(f"Deploying {config_path}...")
    result = subprocess.run(
        ["serve", "deploy", config_path],
        env=os.environ.copy()
    )

    if result.returncode != 0:
        print(f"\nDeploy command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print("\nMonitoring deployment status...\n")

    while True:
        status = serve.status()
        print_status(status)

        all_running, any_failed = check_deployment_complete(status)

        if any_failed:
            print("\n❌ Deployment failed!")
            sys.exit(1)

        if all_running:
            print("\n✅ All services deployed successfully!")
            break

        time.sleep(0.5)


if __name__ == "__main__":
    main()