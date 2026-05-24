"""Run deterministic Mnemon answer quality checks."""

import json

from django.core.management.base import BaseCommand, CommandError

from teramina.agent.evals.mnemon_eval import evaluate_answer_set, load_answer_cases


class Command(BaseCommand):
    help = "Run Mnemon deterministic eval gates against a JSON or JSONL answer file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--answers",
            required=True,
            help="Path to JSON/JSONL file containing answer cases with id and answer fields",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            default=False,
            help="Print machine-readable JSON output",
        )
        parser.add_argument(
            "--allow-fail",
            action="store_true",
            default=False,
            help="Return exit code 0 even when eval gates fail",
        )

    def handle(self, *args, **options):
        cases = load_answer_cases(options["answers"])
        if not cases:
            raise CommandError("No Mnemon answer cases found")

        result = evaluate_answer_set(cases)
        if options["json"]:
            self.stdout.write(json.dumps(result, indent=2, sort_keys=True))
        else:
            self.stdout.write(
                f"Mnemon eval: {result['passed_count']}/{result['total']} passed"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                self.stdout.write(f"- {status} {item['id']}")
                if not item["passed"]:
                    failed = [
                        name for name, passed in item["checks"].items()
                        if not passed
                    ]
                    self.stdout.write(f"  failed_checks: {', '.join(failed)}")
                    if item["invented_numbers"]:
                        self.stdout.write(
                            f"  invented_numbers: {', '.join(item['invented_numbers'])}"
                        )

        if not result["passed"] and not options["allow_fail"]:
            raise CommandError("Mnemon eval failed")
