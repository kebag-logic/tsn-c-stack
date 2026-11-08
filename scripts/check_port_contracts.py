#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Keep public contract names and critical meanings in the integrator guide."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'Target builds': (
        'memcpy',
        'memset',
        'python3 scripts/baremetal.py --work build-rv32 --jobs 16',
        'virt',
    ),
    'Ownership and dispatch': (
        'CTRL_REENTRY_ASSERT',
        'adp_build',
        'adp_poll',
        'adp_reentry_count',
        'ctrl_reentry_assert',
    ),
    'Frames and buffers': (
        'ACMP_OWED_MAX',
        'acmp_change_pending',
        'acmp_poll',
        'adp_poll',
        'departing_coalesced',
        'env->changed',
        'maap_poll',
        'probes_lost',
        'send',
    ),
    'ACMP owed bound': (
        'ACMP_OWED_MAX',
        'acmp_poll',
        'acmp_rx',
        'acmp_rx_ready',
        'bind_waiting',
        'busy_declined',
        'probes_held',
    ),
    'ADP input validation': (
        'adp_rx',
        'control_data_length',
        'discarded',
    ),
    'Callback checklist': (
        'maap_begin',
        'preferred=0',
    ),
    'ADP callbacks and public fields': (
        'ADP_DEPARTING_OWED_MAX',
        'ADP_DRAW_DELAY',
        'ADP_DRAW_NONE',
        'ADP_DRAW_STARTUP',
        'ADP_FRAME_BYTES',
        'ADP_TIMER_ADVERTISE',
        'ADP_TIMER_DELAY',
        'ADP_TIMER_NONE',
        'adp_build',
        'adp_entity',
        'adp_gm_change',
        'adp_link_change',
        'adp_poll',
        'adp_rx',
        'adp_set_current_configuration',
        'adp_set_enable',
        'adp_timer_expired',
        'available_index',
        'available_owed',
        'ctx',
        'current_configuration_index',
        'delay_ms',
        'departing_index',
        'departing_owed',
        'enabled',
        'gptp',
        'interface',
        'link_up',
        'mac',
        'rng',
        'seed',
        'send',
        'timer',
        'timer_start',
        'timer_stop',
    ),
    'ADP counters': (
        'adp_reentry_count',
        'deferred_sends',
        'departing_coalesced',
        'discarded',
        'draws',
        'gm_changed',
        'last_draw',
        'last_draw_ms',
        'stray_expiries',
    ),
    'ACMP callbacks and public fields': (
        'acmp_open',
        'acmp_poll',
        'acmp_source_state',
        'acmp_source_state.asking_failed',
        'acmp_source_state.dest_mac_valid',
        'acmp_tk_kind_changed',
        'acmp_tk_registered',
        'acmp_tk_unregistered',
        'armed=false',
        'bound',
        'bound=false',
        'ctx',
        'deadline_ms',
        'env->changed',
        'env->locked',
        'env->persist',
        'env->source',
        'env->srp',
        'failed',
        'interface',
        'ports->admit',
        'ports->gptp',
        'ports->now_ms',
        'ports->publish',
        'stream_id',
        'stream_moved',
        'started',
        'acmp_set_started',
        'ports->seed',
        'ports->send',
        'ports->timer',
        'sink',
        'stream',
        'talker_entity_id',
    ),
    'ACMP configuration and views': (
        'ACMP_MAX_INTERFACES',
        'acmp_binding',
        'acmp_config.mac',
        'acmp_config.n_interfaces',
        'acmp_config.n_sinks',
        'acmp_config.n_sources',
        'acmp_sink_view.state',
        'acmp_status',
        'acmp_stream',
        'acmp_view',
        'binding',
        'bound',
        'dest_mac',
        'env->changed',
        'probing_status',
        'registering_failed',
        'settled',
        'sink_interface',
        'source_interface',
        'started',
        'stream',
        'stream_id',
        'streaming_wait',
        'talker_discovered',
        'talker_registered',
        'vlan_id',
    ),
    'ACMP machine storage': (
        'acmp.sequence_id',
        'acmp_owed.interface',
        'acmp_sink.probe_controller',
        'admitted',
        'admitted_talker',
        'adp_armed',
        'adp_deadline',
        'bind_waiting',
        'change_owed',
        'disc_available_index',
        'disc_interface_index',
        'disc_running',
        'discovered',
        'env->changed',
        'env->persist',
        'env->srp',
        'frame',
        'in_port',
        'now',
        'now_read',
        'owed',
        'owed_count',
        'owed_head',
        'probe_held',
        'probe_of',
        'probe_retried',
        'probe_seq',
        'probe_talker',
        'probe_talker_uid',
        'release',
        'published_bound',
        'published_started',
        'published_stream',
        'reported',
        'rng',
        'saved',
        'seeded',
        'stream',
        'timer',
        'timer_armed',
        'timer_at',
        'timer_deadline',
        'timer_held',
        'tk_failed',
    ),
    'ACMP counters': (
        'CTRL_REENTRY_ASSERT',
        'adp_ignored',
        'busy_declined',
        'ctrl_reentry_assert',
        'deferred_sends',
        'draws',
        'impossible',
        'last_draw_ms',
        'probe_mismatch',
        'probes_held',
        'probes_lost',
        'reentries',
        'refused_locked',
        'rx_ignored',
        'rx_malformed',
        'unknown_sink',
    ),
    'MAAP callbacks and public fields': (
        'clock',
        'count',
        'ctx',
        'maap_begin',
        'maap_poll',
        'maap_port_operational',
        'maap_release',
        'maap_timer_expired',
        'preferred',
        'range',
        'send',
        'timer_start',
        'timer_stop',
        'valid=true',
    ),
    'MAAP counters': (
        'conflicts',
        'deferred',
        'discarded',
        'overflow',
        'reentries',
        'stale_expiries',
    ),
    'Wire field preconditions': (
        'bytes',
        'wire_be16',
        'wire_be32',
        'wire_be64',
        'wire_put_be',
    ),
    'Persistence and startup': (
        'acmp_adp_rx',
        'acmp_binding_latch',
        'acmp_init',
        'acmp_open',
        'acmp_restore_binding',
        'acmp_restore_rollback',
        'acmp_rx',
        'acmp_set_started',
        'acmp_timer_expired',
        'acmp_tk_kind_changed',
        'acmp_view',
    ),
}

CRITICAL = {
    'ACMP callbacks and public fields': {
        'ports->publish': ('published before promised', 'before each new frame', 'first in `finish`', 'before timers', 'admission, persistence and change notification', 'synchronously before returning, without re-entry'),
        'env->srp': ('starts SRP reservation and listening', 'NULL stops listening', 'clears the stream parameters'),
        'ports->admit': ('ENTITY_AVAILABLE and ENTITY_DEPARTING', 'on bind, unbind and rebind', 'for each restored binding'),
        'bound=false': ("withdraw that sink's admission entry",),
        'acmp_source_state.dest_mac_valid': ('MAAP holds a destination MAC',),
        'acmp_source_state.asking_failed': ('Listener Asking Failed attribute is registered',),
        'acmp_tk_registered': ("sink's settled stream", 'true when the registered Talker attribute is Talker Failed'),
    },
    'ACMP owed bound': {
        'acmp_rx': ('declines each command addressed to this entity', 'before changing state or calling a port',
                    'delivers it again after', 'before it services `acmp_timer_expired`', 'Deliver no later ACMP frame before a kept one',
                    'returns false for refused callback re-entry', 'A BIND_RX needs two free owed slots',
                    'a deferred binding loses no probe', 'This is the redelivery rule the bound below assumes',
                    'which `acmp_rx` declines again'),
        'acmp_rx_ready': ('false inside a port callback', 'leaves the frame in its receive queue', 'needs two free owed slots',
                          'gives the core no sign of it', '`ACMP_OWED_MAX` + 1 + `n_sinks` passes'),
        'bind_waiting': ('which only holds timer probes', 'accepts an owed frame clears it', 'is held instead of owed',
                         'retried at the first timer service 1 ms or more later', 'A refused `acmp_poll` leaves it set',
                         'a BIND_RX declined with no slot free does not set it', 'No other expiry is held'),
        'probes_held': ('A held probe is never lost', 'is held with it', 'after the commands still kept',
                        'through the pass that takes the BIND_RX', 'whatever timer probes fall due meanwhile',
                        'no timer probe is owed ahead of a kept command', 'once for each pass it is held',
                        'cancelled only when its sink stops probing', 'Held probes follow the frames of the last kept command',
                        'These counts assume passes at least 1 ms apart',
                        "its sink's probing does not advance until the probe is owed"),
        'ACMP_OWED_MAX': ('640 bytes on both targets', 'never an error status', 'leaves in pass `ACMP_OWED_MAX` + 1 + f + r',
                          'f counts the frames owed by the kept commands ahead of it',
                          'two frames if it is a BIND_RX that starts a binding',
                          'each refused poll delays every later frame by one pass',
                          'Budget the egress hold for the deepest backlog the port keeps',
                          'a hold of at most 193 - 2 * Q ms meets every timeout'),
    },
    'Ownership and dispatch': {
        'adp_reentry_count': ('Builds without `NDEBUG` assert on re-entry', 'Builds with `NDEBUG` ignore it', 'modulo 2^32'),
    },
}


def check(text):
    headings = list(re.finditer(r'^#{2,3} (.+)$', text, re.M))
    sections = {m[1]: text[m.end():headings[i + 1].start() if i + 1 < len(headings) else len(text)]
                for i, m in enumerate(headings)}
    errors = [heading + ': missing contract name ' + name
              for heading, names in REQUIRED.items() for name in names
              if '`' + name + '`' not in sections.get(heading, '')]
    for heading, contracts in CRITICAL.items():
        paragraphs = sections.get(heading, '').split('\n\n')
        for name, phrases in contracts.items():
            for phrase in phrases:
                if not any('`' + name + '`' in p and phrase in ' '.join(p.split()) for p in paragraphs):
                    errors.append(heading + ': missing contract meaning for ' + name + ': ' + phrase)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    text = (ROOT / 'docs/PORTING.md').read_text()
    errors = check(text)
    if args.selftest:
        if errors:
            raise RuntimeError('unplanted contract guide failed: ' + str(errors))
        for name in {n for names in REQUIRED.values() for n in names}:
            if not check(text.replace('`' + name + '`', '`removed`')):
                raise RuntimeError('missing contract accepted: ' + name)
        print('port contracts: all name-removal controls refused')
        count = 0
        for contracts in CRITICAL.values():
            for name, phrases in contracts.items():
                for phrase in phrases:
                    planted = text.replace(phrase, 'removed meaning')
                    if not check(planted):
                        raise RuntimeError('missing meaning accepted: ' + name + ': ' + phrase)
                    count += 1
        print(f'port contracts: {count} meaning-removal controls refused')
    print('\n'.join(errors) if errors else 'port contracts: callbacks, fields, preconditions and counters present')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
