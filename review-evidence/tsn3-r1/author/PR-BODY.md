[A579]

Closes #3

Discovery frames with an unsupported AVTP version, a truncated ADPDU or an incorrect control length previously entered DELAY from WAITING. The receiver now requires version 0, at least 82 bytes including the untagged Ethernet header, and an 11-bit `control_data_length` of 56. Each refusal increments `discarded` once. Other state and port callbacks stay unchanged in every receive state.

The checks follow [IEEE 1722.1-2021 Figure 6-1, 6.2.2.3 and 6.2.2.6](https://standards.ieee.org/ieee/1722.1/6670/) and [IEEE 1722-2016 4.4.3.4 and 4.4.5.4](https://standards.ieee.org/ieee/1722/5979/). Valid global and own-entity discovery retain the behavior in [Milan v1.2 5.6.3.1 and Table 5.51](https://avnu.org/resource/milan-specification/).

The tests cover disabled, DOWN, DELAY, blocked-output DELAY and WAITING conditions. Hosted checks exercise every unsupported version, short length and incorrect control length. Three named plants remove the new guards. The existing own-target plant checks the valid control. Freestanding checks cover the three reported malformed inputs and valid discovery in all five conditions.

[ADP-01](docs/REQUIREMENTS.md#adp-input-validation), the [porting contract](docs/PORTING.md#adp-input-validation), [deviations](docs/DEVIATIONS.md), [traceability](docs/TRACEABILITY.md) and [test inventory](docs/TESTS.md) are updated. DEV-08 is removed.

Validate with the pinned dependencies in the [verification guide](docs/VERIFICATION.md):

```sh
python3 scripts/validate.py --work build-validation --jobs 16 --graphs
python3 scripts/baremetal.py --work build-rv32 --jobs 16
```

Validation: all 25 hosted gates and both freestanding configurations returned zero. Each hosted compiler ran 388 test instances. Adjusted coverage is 100% for lines and branches. The fresh campaign caught all 327 plants through 356 required killer entries. All three diagrams rendered. The post-commit privacy check passed.
Acceptance item 4 remains the separate [consumer update](https://github.com/kebag-logic/milan-fpga/issues/697).
