# PocketBeagle USB entity

The PocketBeagle 2 bridge connects a USB host to a Milan network.
The host sees a USB audio device with 24 playback and 24 capture channels.
The board carries them in four AAF streams each way, plus one CRF stream each way.

This library supplies the bridge's ADP, ACMP and MAAP cores and its [entity configuration](../configs/pocketbeagle.yaml).
The board image is built in the [board support repository](https://github.com/kebag-logic/ti-sitara-am65x-bsp).
Its control firmware comes from [milan-fpga](https://github.com/kebag-logic/milan-fpga).
That firmware supplies AEM, AECP and the descriptor generator. SRP comes from [lwSRP](https://github.com/kebag-logic/lwSRP).

## Use it

A controller sees one entity with five sources and five sinks.
Bind the four AAF outputs to Milan listeners, and Milan talkers to the four AAF inputs.
Each USB channel always belongs to the same stream channel:

| Stream index | Channels | USB channels | Input clusters | Output clusters |
|---|---|---|---|---|
| 0 | 8 | 1 to 8 | 0 to 7 | 24 to 31 |
| 1 | 8 | 9 to 16 | 8 to 15 | 32 to 39 |
| 2 | 4 | 17 to 20 | 16 to 19 | 40 to 43 |
| 3 | 4 | 21 to 24 | 20 to 23 | 44 to 47 |
| 4 | CRF | none | none | none |

USB host playback feeds the STREAM_OUTPUTs. The STREAM_INPUTs feed USB host capture.
Bind STREAM_INPUT 4 to a CRF talker to follow its media clock.

Choose the media clock with SET_CLOCK_SOURCE on CLOCK_DOMAIN 0.
Source 0 is internal, source 1 is the CRF input, and source 2 + k is AAF input k.

## Stream formats

All streams run at 48 kHz. AAF streams carry 32-bit PCM, six samples per channel in each PDU ([Milan v1.2 6.2][milan]).

| Stream | Current format | Accepted formats |
|---|---|---|
| AAF output 0, 1 | `0x0205022002006000`, 8 channels | That format only. |
| AAF output 2, 3 | `0x0205022001006000`, 4 channels | That format only. |
| AAF input 0, 1 | 8 channels | Every 48 kHz base format, 1 to 8 channels ([Milan v1.2 6.4][milan]). |
| AAF input 2, 3 | 4 channels | Every 48 kHz base format, 1 to 8 channels. |
| CRF, both ways | `0x041060010000BB80` | That format only: one timestamp every 96 samples ([Milan v1.2 7.3.2][milan]). |

An input refuses a format that drops a mapped channel ([Milan v1.2 5.4.2.7][milan]).
Channels past a port's clusters are unmapped ([Milan v1.2 5.3.10.1][milan]).

## Design

The descriptors come from one end-station configuration in the board support repository.
milan-fpga's generator turns it into the AEM image, the ADP fields and the SRP shape.
The [configuration here](../configs/pocketbeagle.yaml) restates only the ADP, ACMP and MAAP facts.
Its model ID is the AEM image's pinned model ID, `0x001BC5C52E47A158`.

```mermaid
flowchart LR
  host[USB host] <--> gadget[24 x 24 USB audio]
  gadget <--> media[Media plane]
  media <--> net[AAF and CRF on Ethernet]
  control[Control plane] --> media
  control --- cores[ADP ACMP MAAP from this library]
  control --- fw[AECP AEM SRP from the firmware]
```

Each AAF stream has its own stream port with mono clusters.
Output ports have one static AUDIO_MAP each. Input ports have none: their maps are dynamic ([Milan v1.2 5.3.3.9][milan]).
The entity has one AVB interface and one clock domain with six clock sources.

A talker declares its stream only once a listener asks ([Milan v1.2 4.3.3.1][milan]).
That is a PROBE_TX_COMMAND within 15 seconds, or a registered Listener attribute.
The TSpecs follow [Milan v1.2 Table 4.4][milan]: 217 octets for 8 channels, 121 for 4 and 29 for CRF.
Each has one frame per class A interval, priority 3 and rank 1.
All five talkers together reserve 59.648 Mb/s, under the 75% class A limit of a 100 Mb/s link.

## Conformance by clause

| Clause | Where | Evidence |
|---|---|---|
| [IEEE 1722.1-2021][atdecc] 6.2, Milan v1.2 5.6 (ADP) | This library | [ADP tests](../tests/test_adp.cpp) and the [entity round trip](../examples/entity_roundtrip.c) on both targets. |
| [IEEE 1722.1-2021][atdecc] 8, Milan v1.2 5.5 (ACMP) | This library | [ACMP tests](../tests/test_acmp.cpp) and the entity round trip with five sinks and five sources. |
| [IEEE 1722-2016][avtp] Annex B (MAAP) | This library | [MAAP tests](../tests/test_maap.cpp) and the entity round trip with five addresses. |
| IEEE 1722.1-2021 7, Milan v1.2 5.3 and 5.4 (AEM, AECP) | Firmware | The board support repository's AECP suite at this shape. |
| Milan v1.2 6 and 7, IEEE 1722-2016 7 and 10 (AAF, CRF) | Media plane | The board support repository's talker, listener and counter suites. |
| [IEEE 802.1Q-2018][dot1q] 35, Milan v1.2 4.3.3 (SRP) | Firmware with lwSRP | The board support repository's SRP suite. |

This page claims no certification. Board measurements are recorded with the board image, not here.

## Validate

Run the entity checks of the [verification kit](VERIFICATION.md):

```sh
python3 scripts/entity_yaml.py --examples --check
python3 scripts/mutation.py --work build-entity-mutations --select entity- --jobs 16
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

The plant `entity-dropped-clock-sink` removes the CRF input from the generated ACMP configuration.
`EntityYaml.AcmpRoundTrip` must catch it.

[milan]: https://avnu.org/resource/milan-specification/
[atdecc]: https://standards.ieee.org/ieee/1722.1/6670/
[avtp]: https://standards.ieee.org/ieee/1722/5979/
[dot1q]: https://standards.ieee.org/ieee/802.1Q/6844/
