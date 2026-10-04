"""Static SVG reports: no scripts, telemetry, external fonts or resources."""
import html
from itertools import pairwise


def plot(series, title, end, markers=(), step=False):
    width, height = 900, 180
    samples = [value for _, points in series for _, value in points]
    low, high = min(samples or [0]), max(samples or [1])
    if high <= low:
        high = low + 1
    def x(at):
        return 50 + 830 * at / max(end, 1)
    def y(value):
        return 135 - 100 * (value-low) / (high-low)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',
             f'<text x="50" y="18">{html.escape(title)}</text>',
             '<path d="M50 30 V135 H880" fill="none" stroke="#bcc4d2"/>',
             f'<text x="2" y="40">{high:.3g}</text><text x="2" y="135">{low:.3g}</text>',
             f'<text x="50" y="175">0 ms</text><text x="795" y="175">{end} ms</text>']
    colors = ['#007d91', '#bc4d15', '#733fc1', '#455572']
    for index, (label, points) in enumerate(series):
        if step and points:
            expanded = [points[0]]
            for previous, current in pairwise(points):
                expanded.extend([(current[0], previous[1]), current])
            points = expanded
        coords = ' '.join(f'{x(at):.2f},{y(value):.2f}' for at, value in points)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{colors[index % 4]}" stroke-width="2"/>')
        parts.append(f'<text x="{50+index*205}" y="155" fill="{colors[index % 4]}">{html.escape(label)}</text>')
    for at, label in markers:
        parts.append(f'<path d="M{x(at):.2f} 30 V135" stroke="#b32626" stroke-dasharray="4 3"/>')
        parts.append(f'<text x="{x(at)+5:.2f}" y="45" fill="#b32626">{html.escape(label)}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def render_report(cases):
    sections = []
    for name, (events, result) in cases.items():
        end = events[-1]['time_ms'] if events else 0
        markers = [(at, 'Fault detected') for at in sorted({e['time_ms'] for e in events if e['kind'] == 'fault'})]
        faults = [(e['time_ms'], e['data']['cause']) for e in events if e['kind'] == 'fault']
        cause_text = ', '.join(f'{html.escape(cause)} at {at} ms' for at, cause in faults) or 'none detected'
        pressure, flow, pump, valve, actual, states = [], [], [], [], [], []
        labels = ['disconnected', 'ready', 'armed', 'running', 'fault', 'recovery_required']
        for e in events:
            at, data = e['time_ms'], e['data']
            if e['kind'] == 'measurement':
                if data['channel'] == 'pressure1':
                    pressure.append((at, data['value']/1000))
                elif data['channel'] == 'flow':
                    flow.append((at, data['value']*60000))
            elif e['kind'] == 'command':
                pump.append((at, data.get('pump', 0)))
                valve.append((at, data.get('valve', 0)))
            elif e['kind'] == 'actuator':
                actual.append((at, data['valve']))
            elif e['kind'] == 'state':
                states.append((at, labels.index(data['state']) if data['state'] in labels else 0))
        evidence = []
        for check in result['checks']:
            for detail in check['details']:
                if 'latency_ms' in detail:
                    evidence.append(f'<tr><td>{html.escape(check["id"])}</td><td>{detail["trigger_ms"]}</td>'
                                    f'<td>{detail["deadline_ms"]}</td><td>{detail["observed_ms"]}</td>'
                                    f'<td>{detail["latency_ms"]}</td><td>{html.escape(check["status"])}</td></tr>')
        sections.append(f'<section><h2>{html.escape(name)} <span class="{result["status"]}">{result["status"]}</span></h2>'
                        f'<p>Observation window: {html.escape(str(result["window_ms"]))} ms. '
                        'Safe command evidence measures issue time. Actual actuator position is a separate observation.</p>'
                        + f'<p>Fault causes: {cause_text}.</p>'
                        + plot([('pressure1', pressure)], 'Pressure (kPa)', end, markers)
                        + plot([('outlet', flow)], 'Flow (L/min)', end, markers)
                        + plot([('pump command', pump), ('valve command', valve), ('actual valve', actual)], 'Commands and valve fraction', end, markers, step=True)
                        + plot([('state code', states)], 'Controller state', end, markers, step=True)
                        + '<p>State codes: 0 disconnected, 1 ready, 2 armed, 3 running, 4 fault, 5 recovery_required.</p>'
                        + '<details><summary>Requirement timeline (ms)</summary><table><tr><th>ID</th><th>Trigger</th><th>Deadline</th><th>Observed</th><th>Latency</th><th>Verdict</th></tr>'
                        + ''.join(evidence) + '</table></details></section>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">' \
        '<title>AbyssBench replay evidence</title><style>body{font:16px system-ui;background:#f4f6fa;color:#182538;margin:0 auto;padding:32px;max-width:1040px}' \
        'section{background:white;padding:24px;margin:24px 0;border-radius:8px}svg{display:block;width:100%;height:auto}svg text{font:12px system-ui}' \
        'table{border-collapse:collapse}td,th{padding:6px 12px;border-bottom:1px solid #ddd}.pass{color:#00705c}.fail{color:#b32626}.inconclusive{color:#755415}' \
        '</style><h1>AbyssBench — controller replay</h1><p><strong>Simulation only.</strong> Synthetic inputs; illustrative uncalibrated fluid model. '
        'Command issuance does not prove mechanical motion. No physical qualification, live model campaign, or practitioner adoption is claimed.</p>' \
        '<p>Same fault schedule: compare freshness_receive with repaired. Clock: single monotonic integer ms. '
        'Finite windows preserve inconclusive obligations.</p>' + ''.join(sections) + '</html>')
