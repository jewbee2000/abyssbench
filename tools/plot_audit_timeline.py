"""Replot archived synthetic evidence; requires optional matplotlib==3.11.2."""
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'evidence/publication-audit'


def main():
    source = AUDIT / 'stuck-valve-events.jsonl'
    events = [json.loads(line) for line in source.read_text().splitlines()]
    commands = [e for e in events if e['kind'] == 'command']
    positions = [e for e in events if e['kind'] == 'actuator']
    onset = next(e['time_ms'] for e in events if e['kind'] == 'injection')
    detection = next(e['time_ms'] for e in events if e['kind'] == 'fault'
                     and e['data']['cause'] == 'valve_mismatch')
    safe = next(e['time_ms'] for e in commands if e['time_ms'] >= detection
                and e['data'] == {'pump': 0.0, 'valve': 1.0})
    assert all(e['data']['valve'] == 0 for e in positions if e['time_ms'] >= onset)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.edgecolor': '#bac4ce', 'text.color': '#172635',
                         'axes.labelcolor': '#172635', 'xtick.color': '#425565',
                         'ytick.color': '#425565', 'svg.fonttype': 'none',
                         'svg.hashsalt': 'abyssbench-stuck-valve-audit'})
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                     gridspec_kw={'height_ratios': [2, 1]})
    fig.subplots_adjust(top=.79, bottom=.19, left=.095, right=.97, hspace=.27)
    fig.text(.095, .93, 'Commanding a valve open does not make it move',
             fontsize=20, weight='bold')
    fig.text(.095, .875, 'AbyssBench | retained stuck-valve trace | synthetic simulation',
             fontsize=12, color='#526777')
    times = [e['time_ms'] for e in commands]
    top.step(times, [e['data']['valve'] for e in commands], where='post',
             label='Valve command', color='#057d88', linewidth=2.7)
    top.plot([e['time_ms'] for e in positions], [e['data']['valve'] for e in positions],
             label='Simulated valve position', color='#c04b21', linewidth=2.5)
    top.set_ylabel('Valve fraction\n0 closed / 1 open')
    top.set_ylim(-.1, 1.25)
    top.set_yticks([0, .5, 1])
    top.legend(loc='upper left', frameon=False, fontsize=11)
    top.annotate(f'Valve stuck closed\n{onset:,} ms', xy=(onset, 0), xytext=(onset-130, .34),
                 fontsize=11, color='#8d3518', arrowprops={'arrowstyle': '->', 'color': '#8d3518'})
    top.annotate(f'Fault detected; open command\n{detection:,} ms', xy=(detection, 1),
                 xytext=(detection+25, .70), fontsize=11, color='#006873',
                 arrowprops={'arrowstyle': '->', 'color': '#006873'})
    bottom.step(times, [e['data']['pump'] for e in commands], where='post',
                color='#53669a', linewidth=2.5)
    bottom.set_ylabel('Pump command\nfraction')
    bottom.set_ylim(-.07, .67)
    bottom.set_yticks([0, .5])
    bottom.annotate(f'Pump-off command at {safe:,} ms', xy=(safe, 0),
                    xytext=(safe+25, .35), fontsize=11, color='#3b4c78',
                    arrowprops={'arrowstyle': '->', 'color': '#3b4c78'})
    for ax in (top, bottom):
        ax.axvspan(onset, detection, color='#f1c891', alpha=.20, zorder=0)
        ax.axvline(onset, color='#c04b21', linestyle=':', linewidth=1)
        ax.axvline(detection, color='#057d88', linestyle=':', linewidth=1)
        ax.grid(axis='y', color='#dce3e9', linewidth=.6, alpha=.8)
        ax.set_xlim(0, events[-1]['time_ms'])
    bottom.set_xticks([0, 250, 500, 750, 1000, 1250, 1500])
    bottom.set_xlabel('Simulation time (ms)', labelpad=10)
    fig.text(.095, .075, 'The controller issues safe commands in the detection tick. The valve remains closed.',
             fontsize=11)
    fig.text(.095, .035, 'Illustrative, uncalibrated model. Timing-contract evidence does not establish physical safety.',
             fontsize=10, color='#526777')
    outputs = []
    for extension in ('png', 'svg'):
        path = AUDIT / f'stuck-valve-timeline.{extension}'
        fig.savefig(path, dpi=160, facecolor='white',
                    metadata={'Date': None} if extension == 'svg' else None)
        if extension == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())
                            + '\n', encoding='utf-8', newline='\n')
        outputs.append(path)
    provenance = {'source': source.relative_to(ROOT).as_posix(),
                  'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'onset_ms': onset, 'detection_ms': detection, 'safe_command_ms': safe,
                  'matplotlib_version': matplotlib.__version__,
                  'outputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},
                  'boundary': 'Replot of original archived synthetic trace, not physical measurement.'}
    (AUDIT / 'figure-provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps(provenance, indent=2))


if __name__ == '__main__':
    main()
