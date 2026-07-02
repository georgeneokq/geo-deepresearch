import sys
import json
import argparse

LEVELS = {
    'INFO': 'notice',
    'WARNING': 'warning',
    'ERROR': 'error'
}

def format_github_annotation(finding: dict, level: str):
    return (
        f'::{LEVELS[level]} '
        f'file={finding["path"]},'
        f'line={finding["start"]["line"]},col={finding["start"]["col"]}'
        f'::{finding["check_id"]}: {finding["extra"]["message"]}'
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('semgrep_results_file', type=str)

    args = parser.parse_args()

    file_path = args.semgrep_results_file

    with open(file_path, 'r') as f:
        data = json.load(f)

    results = data['results']

    errors = []
    warnings = []
    infos = []

    for result in results:
        severity = result['extra']['severity']
        if severity == 'ERROR':
            errors.append(result)
        elif severity == 'WARNING':
            warnings.append(result)
        else:
            infos.append(result)

    for info in infos:
        print(format_github_annotation(info, info['extra']['severity']))

    for warning in warnings:
        print(format_github_annotation(warning, warning['extra']['severity']))

    for error in errors:
        print(format_github_annotation(error, error['extra']['severity']))

    print('======== Semgrep Summary ========')
    print(f'INFO: {len(infos)}')
    print(f'WARNING: {len(warnings)}')
    print(f'ERROR: {len(errors)}')
    print('=================================')

    # If any ERROR level findings, flag it out with exit code 1 for ci workflow to catch
    if errors:
        sys.exit(1)
