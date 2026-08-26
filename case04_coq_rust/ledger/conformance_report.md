# Case 04 — process conformance (C13/C3/C14), post-hoc run

## armA_r5 (arm A, deepseek/deepseek-v4-pro)
- v files: 1
- Admitted/admit: 0
- run-added Axiom/Parameter: 0
- deposits: src/extracted.rs
- deposit src/extracted.rs: unique
- crate hash-lock src/extracted.rs vs deposit: OK
- adapter src/main.rs: 116 lines (cap 200), tokens: legal, mate, stalemate, castl
- adapter skeleton/src/main.rs: 36 lines (cap 200), tokens: legal
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 248
  - {"type":"step_start","timestamp":1787682666953,"sessionID":"ses_fc5cf6779ffe2cGh2PAtkF6Uyu","part":{
  - {"type":"step_start","timestamp":1787682669128,"sessionID":"ses_fc5cf6779ffe2cGh2PAtkF6Uyu","part":{
  - {"type":"tool_use","timestamp":1787682670258,"sessionID":"ses_fc5cf6779ffe2cGh2PAtkF6Uyu","part":{"t
- oracle queries (CLI counter): 117 (cap 5000) -> OK

## armB_r4 (arm B, deepseek/deepseek-v4-pro)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 63
  - {"type":"tool_use","timestamp":1787682669803,"sessionID":"ses_fc5cf67a8ffe00S6HxT6utpCwP","part":{"t
  - {"type":"tool_use","timestamp":1787682672016,"sessionID":"ses_fc5cf67a8ffe00S6HxT6utpCwP","part":{"t
  - {"type":"tool_use","timestamp":1787682707273,"sessionID":"ses_fc5cf67a8ffe00S6HxT6utpCwP","part":{"t
- oracle queries (CLI counter): 542 (cap 5000) -> OK

## armA_r2 (arm A, deepseek/deepseek-v4-pro)
- v files: 3
- Admitted/admit: 0
- run-added Axiom/Parameter: 0
- deposits: src/extracted.rs
- deposit src/extracted.rs: unique
- crate hash-lock src/extracted.rs vs deposit: OK
- adapter src/main.rs: 104 lines (cap 200), tokens: legal, mate, stalemate, castl
- adapter skeleton/src/main.rs: 36 lines (cap 200), tokens: legal
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 59
  - {"type":"tool_use","timestamp":1787682823732,"sessionID":"ses_fc5cf6712ffeb31Kho9i4o016h","part":{"t
  - {"type":"step_start","timestamp":1787682834820,"sessionID":"ses_fc5cf6712ffeb31Kho9i4o016h","part":{
  - {"type":"tool_use","timestamp":1787682841466,"sessionID":"ses_fc5cf6712ffeb31Kho9i4o016h","part":{"t
- oracle queries (CLI counter): 1263 (cap 5000) -> OK

## armB_r5 (arm B, deepseek/deepseek-v4-pro)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 36
  - {"type":"step_finish","timestamp":1787682668761,"sessionID":"ses_fc5cf6548ffen5PR2KKZW2ZjE5","part":
  - {"type":"tool_use","timestamp":1787682690273,"sessionID":"ses_fc5cf6548ffen5PR2KKZW2ZjE5","part":{"t
  - {"type":"step_start","timestamp":1787682702664,"sessionID":"ses_fc5cf6548ffen5PR2KKZW2ZjE5","part":{
- oracle queries (CLI counter): 291 (cap 5000) -> OK

## armA_r3 (arm A, deepseek/deepseek-v4-pro)
- v files: 3
- Admitted/admit: 0
- run-added Axiom/Parameter: 0
- deposits: src/extracted.rs
- deposit src/extracted.rs: unique
- crate hash-lock src/extracted.rs vs deposit: OK
- adapter src/main.rs: 104 lines (cap 200), tokens: legal, mate, stalemate, castl
- adapter skeleton/src/main.rs: 36 lines (cap 200), tokens: legal
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 26
  - {"type":"tool_use","timestamp":1787686178634,"sessionID":"ses_fc59a1c0cffeGqXM0WSY2Z8bTl","part":{"t
  - {"type":"tool_use","timestamp":1787686330988,"sessionID":"ses_fc59a1c0cffeGqXM0WSY2Z8bTl","part":{"t
  - {"type":"step_start","timestamp":1787686331665,"sessionID":"ses_fc59a1c0cffeGqXM0WSY2Z8bTl","part":{
- oracle queries (CLI counter): 248 (cap 5000) -> OK

## armB_r2 (arm B, deepseek/deepseek-v4-pro)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 37
  - {"type":"step_finish","timestamp":1787687018158,"sessionID":"ses_fc58d2a09ffe4fPkuQxC58zw43","part":
  - {"type":"tool_use","timestamp":1787687041499,"sessionID":"ses_fc58d2a09ffe4fPkuQxC58zw43","part":{"t
  - {"type":"tool_use","timestamp":1787687075016,"sessionID":"ses_fc58d2a09ffe4fPkuQxC58zw43","part":{"t
- oracle queries (CLI counter): 233 (cap 5000) -> OK

## armA_r4 (arm A, deepseek/deepseek-v4-pro)
- v files: 2
- Admitted/admit: 0
- run-added Axiom/Parameter: 0
- deposits: skeleton/src/extracted.rs
- deposit skeleton/src/extracted.rs: unique
- crate hash-lock skeleton/src/extracted.rs vs deposit: OK
- adapter skeleton/src/main.rs: 124 lines (cap 200), tokens: legal, mate, stalemate, castl
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 56
  - {"type":"tool_use","timestamp":1787687014553,"sessionID":"ses_fc58d2a22ffeSItN71lBfYmVEL","part":{"t
  - {"type":"tool_use","timestamp":1787687036119,"sessionID":"ses_fc58d2a22ffeSItN71lBfYmVEL","part":{"t
  - {"type":"tool_use","timestamp":1787687039098,"sessionID":"ses_fc58d2a22ffeSItN71lBfYmVEL","part":{"t
- oracle queries (CLI counter): 391 (cap 5000) -> OK

## armB_s1 (arm B, deepseek/deepseek-v4-flash)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-flash (pin deepseek/deepseek-v4-flash) -> OK
- foreign model mentions in transcript: 59
  - {"type":"step_start","timestamp":1787708925618,"sessionID":"ses_fc43fc27bffebAZ9uBYAah6IsM","part":{
  - {"type":"tool_use","timestamp":1787708936417,"sessionID":"ses_fc43fc27bffebAZ9uBYAah6IsM","part":{"t
  - {"type":"tool_use","timestamp":1787708958034,"sessionID":"ses_fc43fc27bffebAZ9uBYAah6IsM","part":{"t
- oracle queries (CLI counter): 1345 (cap 5000) -> OK

## armB_s3 (arm B, deepseek/deepseek-v4-flash)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-flash (pin deepseek/deepseek-v4-flash) -> OK
- foreign model mentions in transcript: 18
  - {"type":"tool_use","timestamp":1787709935451,"sessionID":"ses_fc42f516affeEle34ampz7D2cI","part":{"t
  - {"type":"tool_use","timestamp":1787709937702,"sessionID":"ses_fc42f516affeEle34ampz7D2cI","part":{"t
  - {"type":"tool_use","timestamp":1787709961026,"sessionID":"ses_fc42f516affeEle34ampz7D2cI","part":{"t
- oracle queries (CLI counter): 606 (cap 5000) -> OK

## armB_r3 (arm B, deepseek/deepseek-v4-pro)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 16
  - {"type":"tool_use","timestamp":1787713662053,"sessionID":"ses_fc3f680b3ffeNGK9x5lPdiomWp","part":{"t
  - {"type":"tool_use","timestamp":1787713771482,"sessionID":"ses_fc3f680b3ffeNGK9x5lPdiomWp","part":{"t
  - {"type":"tool_use","timestamp":1787713811715,"sessionID":"ses_fc3f680b3ffeNGK9x5lPdiomWp","part":{"t
- oracle queries (CLI counter): 673 (cap 5000) -> OK

## armB_s2 (arm B, deepseek/deepseek-v4-flash)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-flash (pin deepseek/deepseek-v4-flash) -> OK
- foreign model mentions in transcript: 25
  - {"type":"error","timestamp":1787691341221,"sessionID":"ses_fc54af4a2ffejRG2Rix6Ecqcyc","error":{"nam
  - {"type":"step_start","timestamp":1787719793458,"sessionID":"ses_fc39908f4ffed6SiCvynZTQcUU","part":{
  - {"type":"tool_use","timestamp":1787719795095,"sessionID":"ses_fc39908f4ffed6SiCvynZTQcUU","part":{"t
- oracle queries (CLI counter): 84 (cap 5000) -> OK

## armB_r1 (arm B, deepseek/deepseek-v4-pro)
- .v files in workspace: none
- Rocq hits in transcript: 0
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 17
  - {"type":"error","timestamp":1787691409424,"sessionID":"ses_fc54a0950fferFqRUokRBPvIQh","error":{"nam
  - {"type":"tool_use","timestamp":1787721739547,"sessionID":"ses_fc37bb58dffeoU7bEvvOAIODQv","part":{"t
  - {"type":"tool_use","timestamp":1787721766191,"sessionID":"ses_fc37bb58dffeoU7bEvvOAIODQv","part":{"t
- oracle queries (CLI counter): 342 (cap 5000) -> OK

## armA_r1 (arm A, deepseek/deepseek-v4-pro)
- v files: 1
- Admitted/admit: 0
- run-added Axiom/Parameter: 0
- deposits: src/extracted.rs
- deposit src/extracted.rs: unique
- crate hash-lock src/extracted.rs vs deposit: OK
- adapter src/main.rs: 116 lines (cap 200), tokens: legal, mate, stalemate, castl
- adapter skeleton/src/main.rs: 36 lines (cap 200), tokens: legal
- attempt models (drive.log): deepseek/deepseek-v4-pro (pin deepseek/deepseek-v4-pro) -> OK
- foreign model mentions in transcript: 53
  - {"type":"error","timestamp":1787691409313,"sessionID":"ses_fc54a0949ffeIspzrb7COCGp6I","error":{"nam
  - {"type":"tool_use","timestamp":1787722303352,"sessionID":"ses_fc3728af4ffeBnxWCvjo0cvk6a","part":{"t
  - {"type":"step_start","timestamp":1787722307019,"sessionID":"ses_fc3728af4ffeBnxWCvjo0cvk6a","part":{
- oracle queries (CLI counter): 545 (cap 5000) -> OK
