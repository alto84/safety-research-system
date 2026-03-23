"""CLI entry point for the Safety Research System."""
import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="safety-platform",
        description="Simulated Patient Safety — Cell therapy AE risk estimation",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    serve_parser.add_argument("--reload", action="store_true", help="Auto-reload on changes")
    serve_parser.add_argument("--open", action="store_true", help="Open browser on start")

    # test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument(
        "suite",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "safety", "stress", "validation"],
        help="Test suite to run (default: all)",
    )
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # validate
    subparsers.add_parser("validate", help="Run full validation (lint + format + tests)")

    # predict
    predict_parser = subparsers.add_parser("predict", help="Run risk prediction from CLI")
    predict_parser.add_argument("--ldh", type=float, required=True)
    predict_parser.add_argument("--creatinine", type=float, required=True)
    predict_parser.add_argument("--platelets", type=float, required=True)
    predict_parser.add_argument("--ferritin", type=float, default=500.0)
    predict_parser.add_argument("--fibrinogen", type=float, default=250.0)
    predict_parser.add_argument("--temperature", type=float, default=37.0)
    predict_parser.add_argument("--hemoglobin", type=float, default=12.0)
    predict_parser.add_argument("--anc", type=float, default=2.0)
    predict_parser.add_argument("--crp", type=float, default=5.0)
    predict_parser.add_argument("--disease-burden", type=float, default=0.3)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "serve":
        _cmd_serve(args)
    elif args.command == "test":
        _cmd_test(args)
    elif args.command == "validate":
        _cmd_validate()
    elif args.command == "predict":
        _cmd_predict(args)


def _cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    from src.api.app import app

    if args.open:
        import threading
        import time
        import webbrowser

        def _open_browser() -> None:
            time.sleep(2)
            webbrowser.open(f"http://localhost:{args.port}/psd")

        threading.Thread(target=_open_browser, daemon=True).start()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def _cmd_test(args: argparse.Namespace) -> None:
    import pytest

    test_args = []
    if args.suite == "all":
        test_args.append("tests/")
    else:
        test_args.append(f"tests/{args.suite}/")

    if args.verbose:
        test_args.append("-v")
    else:
        test_args.append("-q")

    sys.exit(pytest.main(test_args))


def _cmd_validate() -> None:
    import subprocess

    result = subprocess.run(["bash", "scripts/validate.sh"], check=False)
    sys.exit(result.returncode)


def _cmd_predict(args: argparse.Namespace) -> None:
    from src.models.ensemble_runner import BiomarkerEnsembleRunner

    runner = BiomarkerEnsembleRunner()
    patient_data = {
        "ldh": args.ldh,
        "creatinine": args.creatinine,
        "platelets": args.platelets,
        "ferritin": args.ferritin,
        "fibrinogen": args.fibrinogen,
        "temperature": args.temperature,
        "hemoglobin": args.hemoglobin,
        "anc": args.anc,
        "crp": args.crp,
        "disease_burden": args.disease_burden,
    }
    result = runner.run(patient_data)
    print(f"Composite Risk Score: {result.composite_score:.2f}")
    print(f"Risk Level: {result.risk_level}")
    for name, score in result.model_scores.items():
        print(f"  {name}: {score:.3f}")


if __name__ == "__main__":
    main()
