# UMI Sniffer - captura ao vivo

- Período: 2026-11-13 10:18:32 → 2026-11-13 10:18:49 (17 s)
- Eventos: 2436 | tópicos/fontes: 28 | campos distintos: 611
- Marcadores: 0

## 1. Tópicos e fontes

| Tópico | O que é (conhecido) | Msgs | Hz | Tamanho (B) | Formato | Campos |
|---|---|---|---|---|---|---|
| 10101_142004 | — (desconhecido) | 8 | 0.50 | 1203 | protobuf | 8 |
| 10102_142004 | Lista de equipamentos (luzes / cargas) | 91 | 5.50 | 30–977 | protobuf | 177 |
| 1202_142004 | — (desconhecido) | 16 | 1.00 | 8 | protobuf | 3 |
| 1301_142004 | — (desconhecido) | 1 | 0.00 | 13 | protobuf | 2 |
| 20101_142004 | — (desconhecido) | 9 | 0.50 | 13 | protobuf | 3 |
| 20102_142004 | — (desconhecido) | 16 | 0.99 | 18 | protobuf | 4 |
| 20103_142004 | — (desconhecido) | 16 | 1.00 | 38 | protobuf | 7 |
| 20201_142004 | — (desconhecido) | 8 | 0.50 | 34 | protobuf | 4 |
| 20202_142004 | — (desconhecido) | 148 | 9.11 | 29–83 | protobuf | 25 |
| 20301_142004 | — (desconhecido) | 14 | 0.87 | 25–117 | protobuf | 11 |
| 20401_142004 | Bateria (info básica) | 16 | 1.00 | 26 | protobuf | 5 |
| 20501_142004 | GPS / posição | 309 | 18.74 | 18–53 | protobuf | 6 |
| 20602_142004 | — (desconhecido) | 82 | 4.95 | 48 | protobuf | 9 |
| 20602_TO_IPC_142004 | — (desconhecido) | 325 | 19.76 | 48 | protobuf | 9 |
| 2202_142004 | — (desconhecido) | 7 | 0.52 | 59 | protobuf | 10 |
| 2203_142004 | — (desconhecido) | 2 | 0.10 | 197 | protobuf | 9 |
| 25101_142004 | Radar (alvos) | 114 | 6.97 | 1004–12313 | protobuf | 147 |
| 40101_142004 | Status geral (~2 KB; SOC/combustível ainda não localizados) | 412 | 25.03 | 2221–2824 | protobuf | 3 |
| 40202_142004 | — (desconhecido) | 1 | 0.00 | 43 | protobuf | 7 |
| 50001_142004 | — (desconhecido) | 17 | 0.98 | 71 | protobuf | 3 |
| 50002_142004 | — (desconhecido) | 95 | 5.77 | 81–1422 | protobuf | 8 |
| 50101_142004 | Propulsão e leme | 115 | 7.00 | 73–80 | protobuf | 16 |
| 51103_142004 | — (desconhecido) | 28 | 1.75 | 15–19 | protobuf | 5 |
| 51301_142004 | — (desconhecido) | 8 | 0.50 | 14 | protobuf | 3 |
| 51302_142004 | — (desconhecido) | 18 | 1.05 | 32–67 | protobuf | 7 |
| avos_tf_tree_142004 | — (desconhecido) | 489 | 29.76 | 55–228 | protobuf | 28 |
| tcp:7 | — (desconhecido) | 34 | 2.00 | 542–812 | json | 51 |
| tcp:8 | — (desconhecido) | 37 | 2.17 | 496–580 | json | 41 |

## 2. Radar: formato das coordenadas

Posição do barco usada como referência: -20.328640, -40.307822

| Interpretação | Maior distância ao barco | Mediana | Plausível (<30 km)? |
|---|---|---|---|
| abs7 | 4962599 m | 4962599 m | não |
| abs7x | 4962599 m | 4962599 m | não |
| abs6 | 4962174 m | 4962174 m | não |
| abs6x | 4962174 m | 4962174 m | não |
| rel_zz | 4317 m | 4317 m | sim |
| rel_int | 8635 m | 8635 m | sim |

**Formato que encaixa: `rel_zz`** (abs7 = zigzag/1e7 igual ao GPS; rel_* = metros relativos ao barco). Rode o UMI Orbit com `--radar-modo rel_zz` para fixar.

| Alvo | Lat | Lon | Distância |
|---|---|---|---|
| radar_22 | -20.356065 | -40.337069 | 4317 m |

## 3. Busca por valor (o que aparece com o número visto no software original)

### Valor 70

Nenhum campo apresentou esse valor (confira se o valor ainda era o mesmo durante a captura).

### Valor 41

| Tópico | Campo | Item | % das amostras | Interpretação | Último | Comportamento |
|---|---|---|---|---|---|---|
| 20202_142004 | 4.2.2 |  | 44% | zigzag×14 | 84 | estado (poucos valores) |

### Valor 34.5

| Tópico | Campo | Item | % das amostras | Interpretação | Último | Comportamento |
|---|---|---|---|---|---|---|
| 20202_142004 | 4.10.10 |  | 5% | inteiro×3 | 34 | estado (poucos valores) |
| 20202_142004 | 4.10.11 |  | 5% | inteiro×3 | 34 | estado (poucos valores) |

### Valor 1200

| Tópico | Campo | Item | % das amostras | Interpretação | Último | Comportamento |
|---|---|---|---|---|---|---|
| 25101_142004 | 4.1.2.2.1 |  | 0% | zigzag×103, inteiro×48 | 31919 | variável contínua |
| 25101_142004 | 4.1.2.2.2 |  | 0% | inteiro×144 | 31839 | variável contínua |

### Valor 3.2

| Tópico | Campo | Item | % das amostras | Interpretação | Último | Comportamento |
|---|---|---|---|---|---|---|
| 20102_142004 | 6.1 |  | 100% | inteiro×16 | 3 | constante |
| 20202_142004 | 4.10.9 |  | 30% | inteiro/10×19 | 32 | estado (poucos valores) |
| 25101_142004 | 4.1.2.2.1 |  | 1% | inteiro/100×261 | 31919 | variável contínua |
| 25101_142004 | 4.1.2.2.2 |  | 1% | inteiro/100×248 | 31839 | variável contínua |

## 5. Itens nomeados (equipamentos, alvos de radar...)

| Tópico | Item | Tradução | Campos (último valor) |
|---|---|---|---|
| 10102_142004 | AIS静默模式 | A + I + S + [静默] + modo (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65589; Estado bruto do equipamento=52 |
| 10102_142004 | Anchor light | Luz de Fundeio | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65600; Estado bruto do equipamento=52 |
| 10102_142004 | GPS定位 | G + P + S + posicionamento (≈) | 7.1.2='0f1c' [4 valores, 4 mud.]; 7.1.4=31 |
| 10102_142004 | Masthead light | Luz do Mastro | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65599; Estado bruto do equipamento=11 |
| 10102_142004 | NUC ↑ light | nuc luz (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65597; Estado bruto do equipamento=52 |
| 10102_142004 | NUC ↓ light | nuc luz (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65598; Estado bruto do equipamento=52 |
| 10102_142004 | Navigation light | Luz de Navegação | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65602; Estado bruto do equipamento=11 |
| 10102_142004 | SVP电池 | S + V + P + bateria (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65590; Estado bruto do equipamento=52 |
| 10102_142004 | SVP绞车上电 | S + V + P + guincho + cima + [电] (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65610; Estado bruto do equipamento=11 |
| 10102_142004 | White | Branca | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65635; Estado bruto do equipamento=52 |
| 10102_142004 | White stern light | Luz de Popa | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65601; Estado bruto do equipamento=11 |
| 10102_142004 | 任务工控机1点动开关 | missão + [工控机] + 1 + [点动] + chave (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65591; Estado bruto do equipamento=52 |
| 10102_142004 | 任务载荷 | Carga útil da missão | 5.1.1=1469478182690 [16 valores, 15 mud.]; ID do equipamento=1560; Estado bruto do equipamento=52 |
| 10102_142004 | 发电机自主管理 | gerador + [自] + principal + [管理] (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65621; Estado bruto do equipamento=11 |
| 10102_142004 | 取消入水限制 |  | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65623; Estado bruto do equipamento=52 |
| 10102_142004 | 右内侧推进器电源 | dir. + interno + [侧] + propulsor + energia (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65606; Estado bruto do equipamento=11 |
| 10102_142004 | 右发电机上电 | dir. + gerador + cima + [电] (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65617; Estado bruto do equipamento=11 |
| 10102_142004 | 右发电机手动模式 | dir. + gerador + manual + modo (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65618; Estado bruto do equipamento=52 |
| 10102_142004 | 右发电机点火 | dir. + gerador + [点火] (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65619; Estado bruto do equipamento=52 |
| 10102_142004 | 右外侧推进器电源 | dir. + externo + [侧] + propulsor + energia (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65605; Estado bruto do equipamento=11 |
| 10102_142004 | 右抽左 | dir. + [抽] + esq. (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65633; Estado bruto do equipamento=52 |
| 10102_142004 | 右片体舱底泵 | dir. + casco (catamarã) + compartimento + [底] + bomba (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65612; Estado bruto do equipamento=52 |
| 10102_142004 | 天线倒伏升 | antena + [倒伏升] (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65586; Estado bruto do equipamento=52 |
| 10102_142004 | 天线倒伏降 | antena + [倒伏降] (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65587; Estado bruto do equipamento=52 |
| 10102_142004 | 左内侧推进器电源 | esq. + interno + [侧] + propulsor + energia (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65604; Estado bruto do equipamento=11 |
| 10102_142004 | 左发电机上电 | esq. + gerador + cima + [电] (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65613; Estado bruto do equipamento=11 |
| 10102_142004 | 左发电机手动模式 | esq. + gerador + manual + modo (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65614; Estado bruto do equipamento=52 |
| 10102_142004 | 左发电机点火 | esq. + gerador + [点火] (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65615; Estado bruto do equipamento=52 |
| 10102_142004 | 左外侧推进器电源 | esq. + externo + [侧] + propulsor + energia (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65603; Estado bruto do equipamento=11 |
| 10102_142004 | 左抽右 | esq. + [抽] + dir. (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65632; Estado bruto do equipamento=52 |
| 10102_142004 | 左片体舱底泵 | esq. + casco (catamarã) + compartimento + [底] + bomba (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65611; Estado bruto do equipamento=52 |
| 10102_142004 | 拖曳系统上电 | [拖曳] + sistema + cima + [电] (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65608; Estado bruto do equipamento=11 |
| 10102_142004 | 智能限制功率 |  | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65624; Estado bruto do equipamento=11 |
| 10102_142004 | 液冷机制冷 |  | 5.1.1=1469478095754 [17 valores, 16 mud.]; ID do equipamento=65807; Estado bruto do equipamento=52 |
| 10102_142004 | 空调冷水机上电 | [空调冷水机] + cima + [电] (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65607; Estado bruto do equipamento=11 |
| 10102_142004 | 空调制冷开关 | [空调制冷] + chave (≈) | 5.1.1=1469478095536 [17 valores, 16 mud.]; ID do equipamento=65628; Estado bruto do equipamento=52 |
| 10102_142004 | 自动油平衡 | Balanceamento Automático | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65634; Estado bruto do equipamento=52 |
| 10102_142004 | 舱内照明灯 | compartimento + interno + [照明] + luz (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65593; Estado bruto do equipamento=52 |
| 10102_142004 | 舱外照明灯(拖曳) | compartimento + externo + [照明] + luz + ( + [拖曳] + ) (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65596; Estado bruto do equipamento=52 |
| 10102_142004 | 舱外照明灯(甲板) | compartimento + externo + [照明] + luz + ( + [甲板] + ) (≈) | 5.1.1=1469478095163 [16 valores, 15 mud.]; ID do equipamento=65595; Estado bruto do equipamento=52 |
| 10102_142004 | 重启感知设备 | [重启感知] + equipamento (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=4294967295; Estado bruto do equipamento=52 |
| 10102_142004 | 重启电子域 |  | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=4294967295; Estado bruto do equipamento=52 |
| 10102_142004 | 重启电池BMS | [重启] + bateria + B + M + S (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=4294967295; Estado bruto do equipamento=52 |
| 10102_142004 | 重启船电 | [重启] + barco + [电] (≈) | 5.1.1=1469478182699 [16 valores, 15 mud.]; ID do equipamento=65622; Estado bruto do equipamento=52 |
| 2202_142004 | motion_ctrl.actuators:cmd_limit:5968777 | motion controle actuators comando limit 5968777 (≈) |  |
| 2202_142004 | motion_ctrl.actuators:cmd_limit:5968778 | motion controle actuators comando limit 5968778 (≈) |  |
| 2202_142004 | motion_ctrl.actuators:cmd_limit:5968779 | motion controle actuators comando limit 5968779 (≈) |  |
| 2202_142004 | motion_ctrl.actuators:cmd_limit:5968780 | motion controle actuators comando limit 5968780 (≈) |  |
| 2203_142004 | motion_ctrl.actuators:cmd_limit:5968777 | motion controle actuators comando limit 5968777 (≈) |  |
| 2203_142004 | motion_ctrl.actuators:cmd_limit:5968778 | motion controle actuators comando limit 5968778 (≈) |  |
| 2203_142004 | motion_ctrl.actuators:cmd_limit:5968779 | motion controle actuators comando limit 5968779 (≈) |  |
| 2203_142004 | motion_ctrl.actuators:cmd_limit:5968780 | motion controle actuators comando limit 5968780 (≈) |  |
| 25101_142004 | bs_72 |  | 5.1.1=1678894530720 [17 valores, 16 mud.]; 5.1.4.1=1678894530720 [17 valores, 16 mud.]; 5.1.4.6=2268612680; 5.1.4.7=436103520; 5.1.6.3=1; 5.1.6.6=4 |
| 25101_142004 | radar_0 | radar 0 (≈) | 5.1.1=1678894524855 [2 valores, 1 mud.]; 5.1.4.1=1678894524855 [2 valores, 1 mud.]; Radar Y (bruto)=5872 [2 valores, 1 mud.]; 5.1.4.6=806268023 [2 valores, 1 mud.]; 5.1.4.7=406493335 [2 valores, 1 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_134 | radar 134 (≈) | 5.1.1=1678894529857 [3 valores, 2 mud.]; 5.1.4.1=1678894529857 [3 valores, 2 mud.]; Radar Y (bruto)=1463 [3 valores, 2 mud.]; 5.1.4.6=806152539 [2 valores, 2 mud.]; 5.1.4.7=406635513 [2 valores, 2 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_150 | radar 150 (≈) | 5.1.1=1678894529855 [7 valores, 6 mud.]; 5.1.4.1=1678894529855 [7 valores, 6 mud.]; Radar Y (bruto)=5204 [7 valores, 6 mud.]; 5.1.4.6=806147559 [5 valores, 6 mud.]; 5.1.4.7=406665863 [7 valores, 6 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_2 | radar 2 (≈) | 5.1.1=1678894529858 [7 valores, 6 mud.]; 5.1.4.1=1678894529858 [7 valores, 6 mud.]; Radar Y (bruto)=5072 [7 valores, 6 mud.]; 5.1.4.6=806162881; 5.1.4.7=406571561 [2 valores, 5 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_22 | radar 22 (≈) | 5.1.1=1678894531256 [64 valores, 81 mud.]; 5.1.4.1=1678894531256 [64 valores, 81 mud.]; Radar X (bruto)=6105 [18 valores, 17 mud.]; Radar Y (bruto)=6105 [18 valores, 17 mud.]; 5.1.4.12=1000 [3 valores, 2 mud.]; 5.1.4.6=806206277 [64 valores, 81 mud.]; 5.1.4.7=406672193 [64 valores, 81 mud.]; 5.1.6.2=1; 5.1.6.3=0.9868 [3 valores, 2 mud.]; 5.1.6.4=400; 5.1.6.5=300; 5.1.6.6=4 |
| 25101_142004 | radar_35 | radar 35 (≈) | 5.1.1=1678894529860 [7 valores, 6 mud.]; 5.1.4.1=1678894529860 [7 valores, 6 mud.]; Radar Y (bruto)=2966 [7 valores, 6 mud.]; 5.1.4.6=806160965 [6 valores, 6 mud.]; 5.1.4.7=406506705 [3 valores, 3 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_378 | radar 378 (≈) | 5.1.1=1678894529856 [3 valores, 2 mud.]; 5.1.4.1=1678894529856 [3 valores, 2 mud.]; Radar Y (bruto)=1414 [3 valores, 2 mud.]; 5.1.4.6=806220335 [3 valores, 2 mud.]; 5.1.4.7=406507969 [2 valores, 1 mud.]; 5.1.6.3=0.01 [2 valores, 1 mud.]; 5.1.6.6=4 |
| 25101_142004 | radar_436 | radar 436 (≈) | 5.1.1=1678894522250 [4 valores, 3 mud.]; 5.1.4.1=1678894522250 [4 valores, 3 mud.]; Radar Y (bruto)=3026 [4 valores, 3 mud.]; 5.1.4.6=806223401 [3 valores, 2 mud.]; 5.1.4.7=406544643 [4 valores, 3 mud.]; 5.1.6.3=0.01 [2 valores, 1 mud.]; 5.1.6.6=4 |
| 25101_142004 | radar_457 | radar 457 (≈) | 5.1.1=1678894507031; 5.1.4.1=1678894507031; Radar Y (bruto)=1289; 5.1.4.6=806167095; 5.1.4.7=406670199; 5.1.6.3=0.012862; 5.1.6.6=4 |
| 25101_142004 | radar_458 | radar 458 (≈) | 5.1.1=1678894529859 [7 valores, 6 mud.]; 5.1.4.1=1678894529859 [7 valores, 6 mud.]; Radar Y (bruto)=2294 [7 valores, 6 mud.]; 5.1.4.6=806173223 [5 valores, 5 mud.]; 5.1.4.7=406562709 [5 valores, 6 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_5 | radar 5 (≈) | 5.1.1=1678894529856 [7 valores, 6 mud.]; 5.1.4.1=1678894529856 [7 valores, 6 mud.]; Radar Y (bruto)=401 [7 valores, 6 mud.]; 5.1.4.6=806199079 [2 valores, 1 mud.]; 5.1.4.7=406574631; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_537 | radar 537 (≈) | 5.1.1=1678894529855 [7 valores, 6 mud.]; 5.1.4.1=1678894529855 [7 valores, 6 mud.]; Radar Y (bruto)=5132 [7 valores, 6 mud.]; 5.1.4.6=806155987 [3 valores, 4 mud.]; 5.1.4.7=406583123 [6 valores, 6 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_576 | radar 576 (≈) | 5.1.1=1678894529537 [4 valores, 3 mud.]; 5.1.4.1=1678894529537 [4 valores, 3 mud.]; Radar Y (bruto)=5548 [4 valores, 3 mud.]; 5.1.4.6=806205801 [4 valores, 3 mud.]; 5.1.4.7=406668601 [3 valores, 2 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_6 | radar 6 (≈) | 5.1.1=1678894529857 [7 valores, 6 mud.]; 5.1.4.1=1678894529857 [7 valores, 6 mud.]; Radar Y (bruto)=306 [7 valores, 6 mud.]; 5.1.4.6=806297137 [2 valores, 3 mud.]; 5.1.4.7=406581855 [4 valores, 4 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_626 | radar 626 (≈) | 5.1.1=1678894529859 [6 valores, 5 mud.]; 5.1.4.1=1678894529859 [6 valores, 5 mud.]; Radar Y (bruto)=1702 [6 valores, 5 mud.]; 5.1.4.6=806210951 [2 valores, 2 mud.]; 5.1.4.7=406530371 [2 valores, 2 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 25101_142004 | radar_640 | radar 640 (≈) | 5.1.1=1678894529861 [3 valores, 2 mud.]; 5.1.4.1=1678894529861 [3 valores, 2 mud.]; Radar Y (bruto)=2682 [3 valores, 2 mud.]; 5.1.4.6=806180693 [2 valores, 1 mud.]; 5.1.4.7=406644365 [2 valores, 1 mud.]; 5.1.6.3=0.01; 5.1.6.6=4 |
| 50002_142004 | air_info |  |  |
| 50002_142004 | lift_info |  |  |
| 50002_142004 | search_light_info | search luz info (≈) |  |
| 50101_142004 | prop |  |  |
| 50101_142004 | steer | leme (≈) |  |
| 51302_142004 | Lower throttle 80% batt < 70% |  |  |
| 51302_142004 | air close because no in water |  |  |
| 51302_142004 | left side not in the water | esquerdo side not in the water (≈) |  |
| 51302_142004 | right side not in the water | direito side not in the water (≈) |  |
| avos_tf_tree_142004 | radar_id | radar id (≈) | 1.1.1=1.6789e+09 [64 valores, 163 mud.]; 1.4.4=1; 1.5.1=-1.5 |
| avos_tf_tree_142004 | usv_enu_3d_id |  | 1.1.1=1.6789e+09 [64 valores, 324 mud.]; 1.4.1=0.99896 [2 valores, 1 mud.]; 1.4.2=0.039378 [2 valores, 1 mud.]; 1.4.3=0.0053838 [2 valores, 1 mud.]; 1.4.4=0.022303 [2 valores, 1 mud.] |
| avos_tf_tree_142004 | usv_ned_id |  | 1.1.1=1.6789e+09 [64 valores, 324 mud.]; 1.4.4=1 |
| avos_tf_tree_142004 | usv_xy_2d_id |  | 1.1.1=1.6789e+09 [64 valores, 324 mud.]; 1.4.3=0.03949 [2 valores, 1 mud.]; 1.4.4=0.99922 [2 valores, 1 mud.] |
| avos_tf_tree_142004 | usv_xy_3d_id |  | 1.1.1=1.6789e+09 [64 valores, 324 mud.]; 1.4.1=-0.022303 [2 valores, 1 mud.]; 1.4.2=-0.0053838 [2 valores, 1 mud.]; 1.4.3=0.039378 [2 valores, 1 mud.]; 1.4.4=0.99896 [2 valores, 1 mud.] |

## 6. Textos encontrados e tradução

| Texto | Tradução | Qualidade | Tópicos |
|---|---|---|---|
|  *can not fire generator because no in water | — | nenhuma | 51302_142004 |
| 0 | — | nenhuma | tcp:8 |
| 123456 | — | nenhuma | tcp:8 |
| 192.168.27.1 | — | nenhuma | tcp:8 |
| 192.168.27.20 | — | nenhuma | tcp:7 |
| 192.168.27.22 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:46 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:47 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:48 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:49 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:50 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:51 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:52 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:53 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:54 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:55 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:56 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:57 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:58 | — | nenhuma | tcp:8 |
| 2026-10-21 23:06:59 | — | nenhuma | tcp:8 |
| 2026-10-21 23:07:00 | — | nenhuma | tcp:8 |
| 2026-10-21 23:07:01 | — | nenhuma | tcp:8 |
| 2026-10-21 23:07:02 | — | nenhuma | tcp:8 |
| 2026-10-21 23:07:03 | — | nenhuma | tcp:8 |
| 800 | — | nenhuma | 2202_142004, 2203_142004 |
| 9e:eb:5b:e8:89:a3 | — | nenhuma | tcp:7 |
| AIS静默模式 | A + I + S + [静默] + modo | parcial | 10102_142004 |
| Anchor light | Luz de Fundeio | exata | 10102_142004 |
| Average power 65.949997 less than 80 and start all generators | average energia 65 949997 less than 80 and start all generators | parcial | 51302_142004 |
| GPS定位 | G + P + S + posicionamento | parcial | 10102_142004 |
| Lower throttle 80% batt < 70% | — | nenhuma | 51302_142004 |
| Masthead light | Luz do Mastro | exata | 10102_142004 |
| NUC ↑ light | nuc luz | parcial | 10102_142004 |
| NUC ↓ light | nuc luz | parcial | 10102_142004 |
| Navigation light | Luz de Navegação | exata | 10102_142004 |
| SVP电池 | S + V + P + bateria | parcial | 10102_142004 |
| SVP绞车上电 | S + V + P + guincho + cima + [电] | parcial | 10102_142004 |
| V2.1.03__Jun 22 2025__16:36:43 | — | nenhuma | tcp:7 |
| White | Branca | exata | 10102_142004 |
| White stern light | Luz de Popa | exata | 10102_142004 |
| air close because no in water | — | nenhuma | 51302_142004 |
| air_info | — | nenhuma | 50002_142004 |
| bs_72 | — | nenhuma | 25101_142004 |
| left side not in the water | esquerdo side not in the water | parcial | 51302_142004 |
| lift_info | — | nenhuma | 50002_142004 |
| motion_ctrl.actuators:cmd_limit:5968777 | motion controle actuators comando limit 5968777 | parcial | 2202_142004, 2203_142004 |
| motion_ctrl.actuators:cmd_limit:5968778 | motion controle actuators comando limit 5968778 | parcial | 2202_142004, 2203_142004 |
| motion_ctrl.actuators:cmd_limit:5968779 | motion controle actuators comando limit 5968779 | parcial | 2202_142004, 2203_142004 |
| motion_ctrl.actuators:cmd_limit:5968780 | motion controle actuators comando limit 5968780 | parcial | 2202_142004, 2203_142004 |
| no fault | no falha | parcial | tcp:8 |
| prop | — | nenhuma | 50101_142004 |
| radar_0 | radar 0 | parcial | 25101_142004 |
| radar_134 | radar 134 | parcial | 25101_142004 |
| radar_150 | radar 150 | parcial | 25101_142004 |
| radar_2 | radar 2 | parcial | 25101_142004 |
| radar_22 | radar 22 | parcial | 25101_142004 |
| radar_35 | radar 35 | parcial | 25101_142004 |
| radar_378 | radar 378 | parcial | 25101_142004 |
| radar_436 | radar 436 | parcial | 25101_142004 |
| radar_457 | radar 457 | parcial | 25101_142004 |
| radar_458 | radar 458 | parcial | 25101_142004 |
| radar_5 | radar 5 | parcial | 25101_142004 |
| radar_537 | radar 537 | parcial | 25101_142004 |
| radar_576 | radar 576 | parcial | 25101_142004 |
| radar_6 | radar 6 | parcial | 25101_142004 |
| radar_626 | radar 626 | parcial | 25101_142004 |
| radar_640 | radar 640 | parcial | 25101_142004 |
| radar_id | radar id | parcial | avos_tf_tree_142004 |
| right side not in the water | direito side not in the water | parcial | 51302_142004 |
| search_light_info | search luz info | parcial | 50002_142004 |
| steer | leme | parcial | 50101_142004 |
| usv_enu_3d_id | — | nenhuma | avos_tf_tree_142004 |
| usv_ned_id | — | nenhuma | avos_tf_tree_142004 |
| usv_xy_2d_id | — | nenhuma | avos_tf_tree_142004 |
| usv_xy_3d_id | — | nenhuma | avos_tf_tree_142004 |
| v1.2.3 | — | nenhuma | tcp:8 |
| v1.2.3-20251114_1010 | — | nenhuma | tcp:8 |
| winch_ctl_param | guincho ctl param | parcial | tcp:7, tcp:8 |
| winch_system_status | guincho system estado | parcial | tcp:7, tcp:8 |
| world_ned_id | — | nenhuma | avos_tf_tree_142004 |
| { 	"air_info" :  	{ 		"param" :  		{ 			"fan_gear" : 3, 			"mode_setting" : 0, 			"temperature_setting" : 20 		}, 		"sensor" :  		{ 			"compressor_current" : 0.0, 			"compressor_speed" : 0, 			"condensing_temperature" : 28.0, 			"evaporation_temperature" : 26.799999237060547, 			"indoor_temperature" : 27.100000381469727, 			"power_voltage" : 0.0, 			"wind_speed_gear" : 0 		}, 		"status" :  		{ 			"alarm_state" : 0, 			"compressor_state" : 0, 			"cooing_state" : 0, 			"fan_high_speed_state" : 0, 			"fan_low_speed_state" : 0, 			"fan_medium_speed_state" : 0, 			"fan_state" : 0, 			"four_way_state" : 0, 			"heating_state" : 0, 			"high_vol_switch_state" : 0, 			"low_vol_switch_state" : 0, 			"machine_state" : 0, 			"thermal_protector_state" : 0, 			"water_pump_state" : 0 		}, 		"warn" :  		{ 			"communication_fault" : 0, 			"compressor_alarm" : 0, 			"compressor_high_temperature" : 0, 			"compressor_overload_alarm" : 0, 			"condensing_probe_fault" : 0, 			"evaporation_probe_fault" : 0, 			"high_pressure_alarm" : 0, 			"high_vol_alarm" : 0, 			"indoor_heat_exchanger_high_temperature_alarm" : 0, 			"indoor_heat_exchanger_low_temperature_alarm" : 0, 			"indoor_probe_fault" : 0, 			"low_pressure_alarm" : 0, 			"low_vol_alarm" : 0, 			"module_high_temperature_alarm" : 0, 			"sea_heat_exchanger_high_temperature_alarm" : 0, 			"sea_heat_exchanger_low_temperature_alarm" : 0 		} 	} } | air info param ventoinha gear 3 modo setting 0 temperature setting 20 sensor compressor atual 0 0 compressor velocidade 0 condensing temperature 28 0 evaporation temperature 26 799999237060547 indoor temperature 27 100000381469727 energia tensão 0 0 wind velocidade gear 0 estado alarme estado 0 compressor estado 0 cooing estado 0 ventoinha high velocidade estado 0 ventoinha low velocidade estado 0 ventoinha medium velocidade estado 0 ventoinha estado 0 four way estado 0 heating estado 0 high tensão switch estado 0 low tensão switch estado 0 machine estado 0 thermal protector estado 0 water bomba estado 0 alarme communication falha 0 compressor alarme 0 compressor high temperature 0 compressor overload alarme 0 condensing probe falha 0 evaporation probe falha 0 high pressão alarme 0 high tensão alarme 0 indoor heat exchanger high temperature alarme 0 indoor heat exchanger low temperature alarme 0 indoor probe falha 0 low pressão alarme 0 low tensão alarme 0 module high temperature alarme 0 sea heat exchanger high temperature alarme 0 sea heat exchanger low temperature alarme 0 | parcial | 50002_142004 |
| {"lift_info":{"1":{"state":0,"deep":0.000000},"0":{"state":4,"deep":0.000000},"force_use":0}} | lift info 1 estado 0 deep 0 000000 0 estado 4 deep 0 000000 force use 0 | parcial | 50002_142004 |
| {"lift_info":{"1":{"state":4,"deep":0.000000},"0":{"state":4,"deep":0.000000},"force_use":0}} | lift info 1 estado 4 deep 0 000000 0 estado 4 deep 0 000000 force use 0 | parcial | 50002_142004 |
| {"search_light_info":{"search_light_status":0}} | search luz info search luz estado 0 | parcial | 50002_142004 |
| 任务工控机1点动开关 | missão + [工控机] + 1 + [点动] + chave | parcial | 10102_142004 |
| 任务载荷 | Carga útil da missão | exata | 10102_142004 |
| 发电机自主管理 | gerador + [自] + principal + [管理] | parcial | 10102_142004 |
| 取消入水限制 | — | nenhuma | 10102_142004 |
| 右内侧推进器电源 | dir. + interno + [侧] + propulsor + energia | parcial | 10102_142004 |
| 右发电机上电 | dir. + gerador + cima + [电] | parcial | 10102_142004 |
| 右发电机手动模式 | dir. + gerador + manual + modo | parcial | 10102_142004 |
| 右发电机点火 | dir. + gerador + [点火] | parcial | 10102_142004 |
| 右外侧推进器电源 | dir. + externo + [侧] + propulsor + energia | parcial | 10102_142004 |
| 右抽左 | dir. + [抽] + esq. | parcial | 10102_142004 |
| 右片体舱底泵 | dir. + casco (catamarã) + compartimento + [底] + bomba | parcial | 10102_142004 |
| 天线倒伏升 | antena + [倒伏升] | parcial | 10102_142004 |
| 天线倒伏降 | antena + [倒伏降] | parcial | 10102_142004 |
| 左内侧推进器电源 | esq. + interno + [侧] + propulsor + energia | parcial | 10102_142004 |
| 左发电机上电 | esq. + gerador + cima + [电] | parcial | 10102_142004 |
| 左发电机手动模式 | esq. + gerador + manual + modo | parcial | 10102_142004 |
| 左发电机点火 | esq. + gerador + [点火] | parcial | 10102_142004 |
| 左外侧推进器电源 | esq. + externo + [侧] + propulsor + energia | parcial | 10102_142004 |
| 左抽右 | esq. + [抽] + dir. | parcial | 10102_142004 |
| 左片体舱底泵 | esq. + casco (catamarã) + compartimento + [底] + bomba | parcial | 10102_142004 |
| 拖曳系统上电 | [拖曳] + sistema + cima + [电] | parcial | 10102_142004 |
| 智能限制功率 | — | nenhuma | 10102_142004 |
| 液冷机制冷 | — | nenhuma | 10102_142004 |
| 空调冷水机上电 | [空调冷水机] + cima + [电] | parcial | 10102_142004 |
| 空调制冷开关 | [空调制冷] + chave | parcial | 10102_142004 |
| 自动油平衡 | Balanceamento Automático | exata | 10102_142004 |
| 舱内照明灯 | compartimento + interno + [照明] + luz | parcial | 10102_142004 |
| 舱外照明灯(拖曳) | compartimento + externo + [照明] + luz + ( + [拖曳] + ) | parcial | 10102_142004 |
| 舱外照明灯(甲板) | compartimento + externo + [照明] + luz + ( + [甲板] + ) | parcial | 10102_142004 |
| 重启感知设备 | [重启感知] + equipamento | parcial | 10102_142004 |
| 重启电子域 | — | nenhuma | 10102_142004 |
| 重启电池BMS | [重启] + bateria + B + M + S | parcial | 10102_142004 |
| 重启船电 | [重启] + barco + [电] | parcial | 10102_142004 |

**Termos chineses sem tradução (acrescente em `TERMOS_ZH` no script):**

- `AIS静默模式` → não reconhecido: 静默
- `SVP绞车上电` → não reconhecido: 电
- `任务工控机1点动开关` → não reconhecido: 工控机, 点动
- `发电机自主管理` → não reconhecido: 自, 管理
- `取消入水限制` → não reconhecido: 取消入水限制
- `右内侧推进器电源` → não reconhecido: 侧
- `右发电机上电` → não reconhecido: 电
- `右发电机点火` → não reconhecido: 点火
- `右外侧推进器电源` → não reconhecido: 侧
- `右抽左` → não reconhecido: 抽
- `右片体舱底泵` → não reconhecido: 底
- `天线倒伏升` → não reconhecido: 倒伏升
- `天线倒伏降` → não reconhecido: 倒伏降
- `左内侧推进器电源` → não reconhecido: 侧
- `左发电机上电` → não reconhecido: 电
- `左发电机点火` → não reconhecido: 点火
- `左外侧推进器电源` → não reconhecido: 侧
- `左抽右` → não reconhecido: 抽
- `左片体舱底泵` → não reconhecido: 底
- `拖曳系统上电` → não reconhecido: 拖曳, 电
- `智能限制功率` → não reconhecido: 智能限制功率
- `液冷机制冷` → não reconhecido: 液冷机制冷
- `空调冷水机上电` → não reconhecido: 空调冷水机, 电
- `空调制冷开关` → não reconhecido: 空调制冷
- `舱内照明灯` → não reconhecido: 照明
- `舱外照明灯(拖曳)` → não reconhecido: 照明, 拖曳
- `舱外照明灯(甲板)` → não reconhecido: 照明, 甲板
- `重启感知设备` → não reconhecido: 重启感知
- `重启电子域` → não reconhecido: 重启电子域
- `重启电池BMS` → não reconhecido: 重启
- `重启船电` → não reconhecido: 重启, 电

_Tradução offline por dicionário: confira os termos marcados como “por partes”._

## 7. Campos por tópico

### `10101_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 8 | 100% | 8 | 1678894516218…1678894530230 | 1678894530230 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 8 | 100% | 1 | — | 4982237 | constante | coordenada? (lat ou lon) zigzag/1e6 = -2.49112..-2.49112 |
| 6.1.1 |  | u64 | 384 | 100% | 14 | 1678894516207…1678894530220 | 1678894530220 | variável contínua | fixed inteiro (bits de status?) |
| 6.1.2 |  | varint | 384 | 100% | 48 | 591677…10686469 | 4326681 | variável contínua | coordenada? (lat ou lon) zigzag/1e7 = -0.53432..0.40337 |
| 6.1.3 |  | varint | 384 | 100% | 1 | — | 8 | constante |  |
| 6.1.4 |  | varint | 384 | 100% | 1 | — | 8 | constante |  |
| 6.1.5 |  | varint | 384 | 100% | 1 | — | 2 | constante |  |
| 6.1.11 |  | bytes | 384 | 100% | 1 | — | '01' | constante |  |

### `10102_142004` — Lista de equipamentos (luzes / cargas)

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 91 | 100% | 64+ | 1469478079420…1469478182699 | 1469478095754 | variável contínua | inteiro negativo em 32 bits? (int32 =599280522) |
| 2 |  | varint | 91 | 100% | 1 | — | 8 | constante |  |
| 5.1.1 | AIS静默模式 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | Anchor light | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | Masthead light | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | NUC ↑ light | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | NUC ↓ light | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | Navigation light | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | SVP电池 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | SVP绞车上电 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | White | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | White stern light | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 任务工控机1点动开关 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 任务载荷 | u64 | 16 | 18% | 16 | 1469478167594…1469478182690 | 1469478182690 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 发电机自主管理 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 取消入水限制 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 右内侧推进器电源 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 右发电机上电 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 右发电机手动模式 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 右发电机点火 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 右外侧推进器电源 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 右抽左 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 右片体舱底泵 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 天线倒伏升 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 天线倒伏降 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 左内侧推进器电源 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 左发电机上电 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 左发电机手动模式 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 左发电机点火 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 左外侧推进器电源 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 左抽右 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 左片体舱底泵 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 拖曳系统上电 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 智能限制功率 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 液冷机制冷 | u64 | 17 | 19% | 17 | 1469478079649…1469478095754 | 1469478095754 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 空调冷水机上电 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 空调制冷开关 | u64 | 17 | 19% | 17 | 1469478079467…1469478095536 | 1469478095536 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 自动油平衡 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 舱内照明灯 | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 舱外照明灯(拖曳) | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 舱外照明灯(甲板) | u64 | 16 | 18% | 16 | 1469478080079…1469478095163 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 重启感知设备 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 重启电子域 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 重启电池BMS | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.1 | 重启船电 | u64 | 16 | 18% | 16 | 1469478167595…1469478182699 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 5.1.2 | AIS静默模式 | varint | 16 | 18% | 1 | — | 65589 | constante | **ID do equipamento** (alta) = 65589 |
| 5.1.2 | Anchor light | varint | 16 | 18% | 1 | — | 65600 | constante | **ID do equipamento** (alta) = 65600 |
| 5.1.2 | Masthead light | varint | 16 | 18% | 1 | — | 65599 | constante | **ID do equipamento** (alta) = 65599 |
| 5.1.2 | NUC ↑ light | varint | 16 | 18% | 1 | — | 65597 | constante | **ID do equipamento** (alta) = 65597 |
| 5.1.2 | NUC ↓ light | varint | 16 | 18% | 1 | — | 65598 | constante | **ID do equipamento** (alta) = 65598 |
| 5.1.2 | Navigation light | varint | 16 | 18% | 1 | — | 65602 | constante | **ID do equipamento** (alta) = 65602 |
| 5.1.2 | SVP电池 | varint | 16 | 18% | 1 | — | 65590 | constante | **ID do equipamento** (alta) = 65590 |
| 5.1.2 | SVP绞车上电 | varint | 16 | 18% | 1 | — | 65610 | constante | **ID do equipamento** (alta) = 65610 |
| 5.1.2 | White | varint | 16 | 18% | 1 | — | 65635 | constante | **ID do equipamento** (alta) = 65635 |
| 5.1.2 | White stern light | varint | 16 | 18% | 1 | — | 65601 | constante | **ID do equipamento** (alta) = 65601 |
| 5.1.2 | 任务工控机1点动开关 | varint | 16 | 18% | 1 | — | 65591 | constante | **ID do equipamento** (alta) = 65591 |
| 5.1.2 | 任务载荷 | varint | 16 | 18% | 1 | — | 1560 | constante | **ID do equipamento** (alta) = 1560 |
| 5.1.2 | 发电机自主管理 | varint | 16 | 18% | 1 | — | 65621 | constante | **ID do equipamento** (alta) = 65621 |
| 5.1.2 | 取消入水限制 | varint | 16 | 18% | 1 | — | 65623 | constante | **ID do equipamento** (alta) = 65623 |
| 5.1.2 | 右内侧推进器电源 | varint | 16 | 18% | 1 | — | 65606 | constante | **ID do equipamento** (alta) = 65606 |
| 5.1.2 | 右发电机上电 | varint | 16 | 18% | 1 | — | 65617 | constante | **ID do equipamento** (alta) = 65617 |
| 5.1.2 | 右发电机手动模式 | varint | 16 | 18% | 1 | — | 65618 | constante | **ID do equipamento** (alta) = 65618 |
| 5.1.2 | 右发电机点火 | varint | 16 | 18% | 1 | — | 65619 | constante | **ID do equipamento** (alta) = 65619 |
| 5.1.2 | 右外侧推进器电源 | varint | 16 | 18% | 1 | — | 65605 | constante | **ID do equipamento** (alta) = 65605 |
| 5.1.2 | 右抽左 | varint | 16 | 18% | 1 | — | 65633 | constante | **ID do equipamento** (alta) = 65633 |
| 5.1.2 | 右片体舱底泵 | varint | 16 | 18% | 1 | — | 65612 | constante | **ID do equipamento** (alta) = 65612 |
| 5.1.2 | 天线倒伏升 | varint | 16 | 18% | 1 | — | 65586 | constante | **ID do equipamento** (alta) = 65586 |
| 5.1.2 | 天线倒伏降 | varint | 16 | 18% | 1 | — | 65587 | constante | **ID do equipamento** (alta) = 65587 |
| 5.1.2 | 左内侧推进器电源 | varint | 16 | 18% | 1 | — | 65604 | constante | **ID do equipamento** (alta) = 65604 |
| 5.1.2 | 左发电机上电 | varint | 16 | 18% | 1 | — | 65613 | constante | **ID do equipamento** (alta) = 65613 |
| 5.1.2 | 左发电机手动模式 | varint | 16 | 18% | 1 | — | 65614 | constante | **ID do equipamento** (alta) = 65614 |
| 5.1.2 | 左发电机点火 | varint | 16 | 18% | 1 | — | 65615 | constante | **ID do equipamento** (alta) = 65615 |
| 5.1.2 | 左外侧推进器电源 | varint | 16 | 18% | 1 | — | 65603 | constante | **ID do equipamento** (alta) = 65603 |
| 5.1.2 | 左抽右 | varint | 16 | 18% | 1 | — | 65632 | constante | **ID do equipamento** (alta) = 65632 |
| 5.1.2 | 左片体舱底泵 | varint | 16 | 18% | 1 | — | 65611 | constante | **ID do equipamento** (alta) = 65611 |
| 5.1.2 | 拖曳系统上电 | varint | 16 | 18% | 1 | — | 65608 | constante | **ID do equipamento** (alta) = 65608 |
| 5.1.2 | 智能限制功率 | varint | 16 | 18% | 1 | — | 65624 | constante | **ID do equipamento** (alta) = 65624 |
| 5.1.2 | 液冷机制冷 | varint | 17 | 19% | 1 | — | 65807 | constante | **ID do equipamento** (alta) = 65807 |
| 5.1.2 | 空调冷水机上电 | varint | 16 | 18% | 1 | — | 65607 | constante | **ID do equipamento** (alta) = 65607 |
| 5.1.2 | 空调制冷开关 | varint | 17 | 19% | 1 | — | 65628 | constante | **ID do equipamento** (alta) = 65628 |
| 5.1.2 | 自动油平衡 | varint | 16 | 18% | 1 | — | 65634 | constante | **ID do equipamento** (alta) = 65634 |
| 5.1.2 | 舱内照明灯 | varint | 16 | 18% | 1 | — | 65593 | constante | **ID do equipamento** (alta) = 65593 |
| 5.1.2 | 舱外照明灯(拖曳) | varint | 16 | 18% | 1 | — | 65596 | constante | **ID do equipamento** (alta) = 65596 |
| 5.1.2 | 舱外照明灯(甲板) | varint | 16 | 18% | 1 | — | 65595 | constante | **ID do equipamento** (alta) = 65595 |
| 5.1.2 | 重启感知设备 | varint | 16 | 18% | 1 | — | 4294967295 | constante | **ID do equipamento** (alta) = 4294967295; inteiro negativo em 32 bits? (int32 =-1) |
| 5.1.2 | 重启电子域 | varint | 16 | 18% | 1 | — | 4294967295 | constante | **ID do equipamento** (alta) = 4294967295; inteiro negativo em 32 bits? (int32 =-1) |
| 5.1.2 | 重启电池BMS | varint | 16 | 18% | 1 | — | 4294967295 | constante | **ID do equipamento** (alta) = 4294967295; inteiro negativo em 32 bits? (int32 =-1) |
| 5.1.2 | 重启船电 | varint | 16 | 18% | 1 | — | 65622 | constante | **ID do equipamento** (alta) = 65622 |
| 5.1.3 | AIS静默模式 | str | 16 | 18% | 1 | — | 'AIS静默模式' | texto (constante) | **Nome do equipamento** (alta) = 'AIS静默模式'; ≈ A + I + S + [静默] + modo (por partes); sem tradução: 静默 |
| 5.1.3 | Anchor light | str | 16 | 18% | 1 | — | 'Anchor light' | texto (constante) | **Nome do equipamento** (alta) = 'Anchor light'; ≈ Luz de Fundeio |
| 5.1.3 | Masthead light | str | 16 | 18% | 1 | — | 'Masthead light' | texto (constante) | **Nome do equipamento** (alta) = 'Masthead light'; ≈ Luz do Mastro |
| 5.1.3 | NUC ↑ light | str | 16 | 18% | 1 | — | 'NUC ↑ light' | texto (constante) | **Nome do equipamento** (alta) = 'NUC ↑ light'; ≈ nuc luz (por partes) |
| 5.1.3 | NUC ↓ light | str | 16 | 18% | 1 | — | 'NUC ↓ light' | texto (constante) | **Nome do equipamento** (alta) = 'NUC ↓ light'; ≈ nuc luz (por partes) |
| 5.1.3 | Navigation light | str | 16 | 18% | 1 | — | 'Navigation light' | texto (constante) | **Nome do equipamento** (alta) = 'Navigation light'; ≈ Luz de Navegação |
| 5.1.3 | SVP电池 | str | 16 | 18% | 1 | — | 'SVP电池' | texto (constante) | **Nome do equipamento** (alta) = 'SVP电池'; ≈ S + V + P + bateria (por partes) |
| 5.1.3 | SVP绞车上电 | str | 16 | 18% | 1 | — | 'SVP绞车上电' | texto (constante) | **Nome do equipamento** (alta) = 'SVP绞车上电'; ≈ S + V + P + guincho + cima + [电] (por partes); sem tradução: 电 |
| 5.1.3 | White | str | 16 | 18% | 1 | — | 'White' | texto (constante) | **Nome do equipamento** (alta) = 'White'; ≈ Branca |
| 5.1.3 | White stern light | str | 16 | 18% | 1 | — | 'White stern light' | texto (constante) | **Nome do equipamento** (alta) = 'White stern light'; ≈ Luz de Popa |
| 5.1.3 | 任务工控机1点动开关 | str | 16 | 18% | 1 | — | '任务工控机1点动开关' | texto (constante) | **Nome do equipamento** (alta) = '任务工控机1点动开关'; ≈ missão + [工控机] + 1 + [点动] + chave (por partes); sem tradução: 工控机, 点动 |
| 5.1.3 | 任务载荷 | str | 16 | 18% | 1 | — | '任务载荷' | texto (constante) | **Nome do equipamento** (alta) = '任务载荷'; ≈ Carga útil da missão |
| 5.1.3 | 发电机自主管理 | str | 16 | 18% | 1 | — | '发电机自主管理' | texto (constante) | **Nome do equipamento** (alta) = '发电机自主管理'; ≈ gerador + [自] + principal + [管理] (por partes); sem tradução: 自, 管理 |
| 5.1.3 | 取消入水限制 | str | 16 | 18% | 1 | — | '取消入水限制' | texto (constante) | **Nome do equipamento** (alta) = '取消入水限制'; sem tradução: 取消入水限制 |
| 5.1.3 | 右内侧推进器电源 | str | 16 | 18% | 1 | — | '右内侧推进器电源' | texto (constante) | **Nome do equipamento** (alta) = '右内侧推进器电源'; ≈ dir. + interno + [侧] + propulsor + energia (por partes); sem tradução: 侧 |
| 5.1.3 | 右发电机上电 | str | 16 | 18% | 1 | — | '右发电机上电' | texto (constante) | **Nome do equipamento** (alta) = '右发电机上电'; ≈ dir. + gerador + cima + [电] (por partes); sem tradução: 电 |
| 5.1.3 | 右发电机手动模式 | str | 16 | 18% | 1 | — | '右发电机手动模式' | texto (constante) | **Nome do equipamento** (alta) = '右发电机手动模式'; ≈ dir. + gerador + manual + modo (por partes) |
| 5.1.3 | 右发电机点火 | str | 16 | 18% | 1 | — | '右发电机点火' | texto (constante) | **Nome do equipamento** (alta) = '右发电机点火'; ≈ dir. + gerador + [点火] (por partes); sem tradução: 点火 |
| 5.1.3 | 右外侧推进器电源 | str | 16 | 18% | 1 | — | '右外侧推进器电源' | texto (constante) | **Nome do equipamento** (alta) = '右外侧推进器电源'; ≈ dir. + externo + [侧] + propulsor + energia (por partes); sem tradução: 侧 |
| 5.1.3 | 右抽左 | str | 16 | 18% | 1 | — | '右抽左' | texto (constante) | **Nome do equipamento** (alta) = '右抽左'; ≈ dir. + [抽] + esq. (por partes); sem tradução: 抽 |
| 5.1.3 | 右片体舱底泵 | str | 16 | 18% | 1 | — | '右片体舱底泵' | texto (constante) | **Nome do equipamento** (alta) = '右片体舱底泵'; ≈ dir. + casco (catamarã) + compartimento + [底] + bomba (por partes); sem tradução: 底 |
| 5.1.3 | 天线倒伏升 | str | 16 | 18% | 1 | — | '天线倒伏升' | texto (constante) | **Nome do equipamento** (alta) = '天线倒伏升'; ≈ antena + [倒伏升] (por partes); sem tradução: 倒伏升 |
| 5.1.3 | 天线倒伏降 | str | 16 | 18% | 1 | — | '天线倒伏降' | texto (constante) | **Nome do equipamento** (alta) = '天线倒伏降'; ≈ antena + [倒伏降] (por partes); sem tradução: 倒伏降 |
| 5.1.3 | 左内侧推进器电源 | str | 16 | 18% | 1 | — | '左内侧推进器电源' | texto (constante) | **Nome do equipamento** (alta) = '左内侧推进器电源'; ≈ esq. + interno + [侧] + propulsor + energia (por partes); sem tradução: 侧 |
| 5.1.3 | 左发电机上电 | str | 16 | 18% | 1 | — | '左发电机上电' | texto (constante) | **Nome do equipamento** (alta) = '左发电机上电'; ≈ esq. + gerador + cima + [电] (por partes); sem tradução: 电 |
| 5.1.3 | 左发电机手动模式 | str | 16 | 18% | 1 | — | '左发电机手动模式' | texto (constante) | **Nome do equipamento** (alta) = '左发电机手动模式'; ≈ esq. + gerador + manual + modo (por partes) |
| 5.1.3 | 左发电机点火 | str | 16 | 18% | 1 | — | '左发电机点火' | texto (constante) | **Nome do equipamento** (alta) = '左发电机点火'; ≈ esq. + gerador + [点火] (por partes); sem tradução: 点火 |
| 5.1.3 | 左外侧推进器电源 | str | 16 | 18% | 1 | — | '左外侧推进器电源' | texto (constante) | **Nome do equipamento** (alta) = '左外侧推进器电源'; ≈ esq. + externo + [侧] + propulsor + energia (por partes); sem tradução: 侧 |
| 5.1.3 | 左抽右 | str | 16 | 18% | 1 | — | '左抽右' | texto (constante) | **Nome do equipamento** (alta) = '左抽右'; ≈ esq. + [抽] + dir. (por partes); sem tradução: 抽 |
| 5.1.3 | 左片体舱底泵 | str | 16 | 18% | 1 | — | '左片体舱底泵' | texto (constante) | **Nome do equipamento** (alta) = '左片体舱底泵'; ≈ esq. + casco (catamarã) + compartimento + [底] + bomba (por partes); sem tradução: 底 |
| 5.1.3 | 拖曳系统上电 | str | 16 | 18% | 1 | — | '拖曳系统上电' | texto (constante) | **Nome do equipamento** (alta) = '拖曳系统上电'; ≈ [拖曳] + sistema + cima + [电] (por partes); sem tradução: 拖曳, 电 |
| 5.1.3 | 智能限制功率 | str | 16 | 18% | 1 | — | '智能限制功率' | texto (constante) | **Nome do equipamento** (alta) = '智能限制功率'; sem tradução: 智能限制功率 |
| 5.1.3 | 液冷机制冷 | str | 17 | 19% | 1 | — | '液冷机制冷' | texto (constante) | **Nome do equipamento** (alta) = '液冷机制冷'; sem tradução: 液冷机制冷 |
| 5.1.3 | 空调冷水机上电 | str | 16 | 18% | 1 | — | '空调冷水机上电' | texto (constante) | **Nome do equipamento** (alta) = '空调冷水机上电'; ≈ [空调冷水机] + cima + [电] (por partes); sem tradução: 空调冷水机, 电 |
| 5.1.3 | 空调制冷开关 | str | 17 | 19% | 1 | — | '空调制冷开关' | texto (constante) | **Nome do equipamento** (alta) = '空调制冷开关'; ≈ [空调制冷] + chave (por partes); sem tradução: 空调制冷 |
| 5.1.3 | 自动油平衡 | str | 16 | 18% | 1 | — | '自动油平衡' | texto (constante) | **Nome do equipamento** (alta) = '自动油平衡'; ≈ Balanceamento Automático |
| 5.1.3 | 舱内照明灯 | str | 16 | 18% | 1 | — | '舱内照明灯' | texto (constante) | **Nome do equipamento** (alta) = '舱内照明灯'; ≈ compartimento + interno + [照明] + luz (por partes); sem tradução: 照明 |
| 5.1.3 | 舱外照明灯(拖曳) | str | 16 | 18% | 1 | — | '舱外照明灯(拖曳)' | texto (constante) | **Nome do equipamento** (alta) = '舱外照明灯(拖曳)'; ≈ compartimento + externo + [照明] + luz + ( + [拖曳] + ) (por partes); sem tradução: 照明, 拖曳 |
| 5.1.3 | 舱外照明灯(甲板) | str | 16 | 18% | 1 | — | '舱外照明灯(甲板)' | texto (constante) | **Nome do equipamento** (alta) = '舱外照明灯(甲板)'; ≈ compartimento + externo + [照明] + luz + ( + [甲板] + ) (por partes); sem tradução: 照明, 甲板 |
| 5.1.3 | 重启感知设备 | str | 16 | 18% | 1 | — | '重启感知设备' | texto (constante) | **Nome do equipamento** (alta) = '重启感知设备'; ≈ [重启感知] + equipamento (por partes); sem tradução: 重启感知 |
| 5.1.3 | 重启电子域 | str | 16 | 18% | 1 | — | '重启电子域' | texto (constante) | **Nome do equipamento** (alta) = '重启电子域'; sem tradução: 重启电子域 |
| 5.1.3 | 重启电池BMS | str | 16 | 18% | 1 | — | '重启电池BMS' | texto (constante) | **Nome do equipamento** (alta) = '重启电池BMS'; ≈ [重启] + bateria + B + M + S (por partes); sem tradução: 重启 |
| 5.1.3 | 重启船电 | str | 16 | 18% | 1 | — | '重启船电' | texto (constante) | **Nome do equipamento** (alta) = '重启船电'; ≈ [重启] + barco + [电] (por partes); sem tradução: 重启, 电 |
| 5.1.5 | AIS静默模式 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | Anchor light | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | Masthead light | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | NUC ↑ light | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | NUC ↓ light | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | Navigation light | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | SVP电池 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | SVP绞车上电 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | White | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | White stern light | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 任务工控机1点动开关 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 任务载荷 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 发电机自主管理 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 取消入水限制 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 右内侧推进器电源 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 右发电机上电 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 右发电机手动模式 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 右发电机点火 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 右外侧推进器电源 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 右抽左 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 右片体舱底泵 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 天线倒伏升 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 天线倒伏降 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 左内侧推进器电源 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 左发电机上电 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 左发电机手动模式 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 左发电机点火 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 左外侧推进器电源 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 左抽右 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 左片体舱底泵 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 拖曳系统上电 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 智能限制功率 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 液冷机制冷 | varint | 17 | 19% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 空调冷水机上电 | varint | 16 | 18% | 1 | — | 11 | constante | **Estado bruto do equipamento** (média) = 11 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 空调制冷开关 | varint | 17 | 19% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 自动油平衡 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 舱内照明灯 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 舱外照明灯(拖曳) | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 舱外照明灯(甲板) | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 重启感知设备 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 重启电子域 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 重启电池BMS | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 5.1.5 | 重启船电 | varint | 16 | 18% | 1 | — | 52 | constante | **Estado bruto do equipamento** (média) = 52 — significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando |
| 7.1.2 | GPS定位 | bytes | 9 | 10% | 4 | — | '0f1c' | estado (poucos valores) |  |
| 7.1.3 | GPS定位 | str | 9 | 10% | 1 | — | 'GPS定位' | texto (constante) | ≈ G + P + S + posicionamento (por partes) |
| 7.1.4 | GPS定位 | varint | 9 | 10% | 1 | — | 31 | constante |  |

### `1202_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 2 |  | varint | 16 | 100% | 1 | — | 8 | constante |  |
| 3 |  | varint | 16 | 100% | 1 | — | 9 | constante |  |
| 6.1 |  | varint | 16 | 100% | 1 | — | 2 | constante |  |

### `1301_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 1 | 100% | 1 | — | 1678894527397 | poucas amostras | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 1 | 100% | 1 | — | 7 | poucas amostras |  |

### `20101_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 9 | 100% | 9 | 1678894515382…1678894531402 | 1678894531402 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 9 | 100% | 1 | — | 7 | constante |  |
| 5.1 |  | varint | 9 | 100% | 1 | — | 4 | constante |  |

### `20102_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 16 | 100% | 16 | 1469478080129…1469478095213 | 1469478095213 | contador/tempo | inteiro negativo em 32 bits? (int32 =599279981) |
| 2 |  | varint | 16 | 100% | 1 | — | 10686469 | constante | coordenada? (lat ou lon) zigzag/1e7 = -0.53432..-0.53432 |
| 6.1 |  | varint | 16 | 100% | 1 | — | 3 | constante |  |
| 6.2 |  | varint | 16 | 100% | 1 | — | 4 | constante |  |

### `20103_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 16 | 100% | 16 | 1794575913386…1794575928396 | 1794575928396 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 16 | 100% | 1 | — | 72 | constante |  |
| 4.1.1 |  | u64 | 16 | 100% | 16 | 1794575913386…1794575928396 | 1794575928396 | contador/tempo | fixed inteiro (bits de status?) |
| 4.1.2 |  | varint | 16 | 100% | 1 | — | 72 | constante |  |
| 4.1.6 |  | varint | 16 | 100% | 1 | — | 2268612680 | constante | coordenada? (lat ou lon) zigzag/1e7 = 113.43063..113.43063 |
| 4.1.7 |  | varint | 16 | 100% | 1 | — | 436103520 | constante | coordenada? (lat ou lon) zigzag/1e7 = 21.80518..21.80518 |
| 4.2 |  | varint | 16 | 100% | 1 | — | 4 | constante |  |

### `20201_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 8 | 100% | 8 | 1678894516218…1678894530230 | 1678894530230 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 8 | 100% | 1 | — | 4982237 | constante | coordenada? (lat ou lon) zigzag/1e6 = -2.49112..-2.49112 |
| 6.1.1 |  | u64 | 8 | 100% | 8 | 1678894516218…1678894530230 | 1678894530230 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 6.1.3 |  | u64 | 8 | 100% | 1 | — | 101 | constante | fixed inteiro (bits de status?) |

### `20202_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 148 | 100% | 64+ | 1469478079462…1469478182699 | 1469478095604 | variável contínua | inteiro negativo em 32 bits? (int32 =599280372) |
| 2 |  | varint | 148 | 100% | 1 | — | 8 | constante |  |
| 4.1.1 |  | varint | 64 | 11% | 4 | 8067429…8132966 | 8067429 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.06648..4.06648 |
| 4.1.2 |  | varint | 64 | 11% | 5 | 124…168 | 139 | estado (poucos valores) |  |
| 4.1.3 |  | varint | 64 | 11% | 4 | 1340…5260 | 5260 | estado (poucos valores) |  |
| 4.1.4 |  | varint | 32 | 11% | 8 | 469…640 | 469 | estado (poucos valores) |  |
| 4.2.1 |  | varint | 32 | 11% | 2 | 8591867…8591868 | 8591868 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.29593..4.29593 |
| 4.2.2 |  | varint | 32 | 11% | 2 | 82…84 | 84 | estado (poucos valores) |  |
| 4.3.2.1 |  | varint | 102 | 11% | 6 | 6886881…7214561 | 6952417 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60728..-3.44344 |
| 4.3.2.2 |  | varint | 102 | 11% | 4 | 504…570 | 526 | estado (poucos valores) |  |
| 4.3.3.1 |  | varint | 102 | 11% | 6 | 6886931…7214611 | 6952467 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60731..-3.44347 |
| 4.3.3.2 |  | varint | 102 | 11% | 6 | 292…364 | 348 | estado (poucos valores) |  |
| 4.3.4.1 |  | varint | 102 | 11% | 6 | 6886831…7214511 | 6952367 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60726..-3.44342 |
| 4.3.5.1 |  | varint | 102 | 11% | 6 | 6887061…7214741 | 7149205 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60737..-3.44353 |
| 4.8.1 |  | varint | 32 | 11% | 2 | 8657353…8657354 | 8657353 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.32868..4.32868 |
| 4.8.4 |  | varint | 32 | 11% | 2 | 36105…40749 | 40749 | estado (poucos valores) |  |
| 4.8.5 |  | varint | 32 | 11% | 2 | 25…27 | 25 | estado (poucos valores) |  |
| 4.8.7 |  | varint | 32 | 11% | 1 | — | 130 | constante |  |
| 4.9.1 |  | varint | 48 | 11% | 3 | 8722919…8722921 | 8722919 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.36146..4.36146 |
| 4.10.1 |  | varint | 64 | 11% | 4 | 5968877…5968880 | 5968877 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -2.98444..2.98444 |
| 4.10.3 |  | varint | 64 | 11% | 3 | 523…525 | 524 | estado (poucos valores) |  |
| 4.10.9 |  | varint | 64 | 11% | 3 | 30…32 | 32 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |
| 4.10.10 |  | varint | 64 | 11% | 5 | 27…34 | 34 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |
| 4.10.11 |  | varint | 64 | 11% | 5 | 27…34 | 34 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |
| 4.10.12 |  | varint | 64 | 11% | 2 | 62…63 | 63 | estado (poucos valores) |  |

### `20301_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 14 | 100% | 8 | 1678894515596…1678894530616 | 1678894530616 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 14 | 100% | 2 | 7…657211 | 657211 | estado (poucos valores) |  |
| 3 |  | varint | 12 | 86% | 1 | — | 72 | constante |  |
| 4.1.1 |  | f32 | 6 | 43% | 2 | 9.5053…10.65 | 10.65 | estado (poucos valores) | 0-100: percentual ou temperatura? |
| 4.1.2 |  | f32 | 6 | 43% | 6 | 1793.9…1808.9 | 1808.9 | estado (poucos valores) |  |
| 4.2.1 |  | f32 | 6 | 43% | 2 | 4.2215e+05…4.2215e+05 | 4.2215e+05 | estado (poucos valores) |  |
| 4.2.2 |  | f32 | 6 | 43% | 6 | 1.445e+06…1.445e+06 | 1.445e+06 | estado (poucos valores) |  |
| 6.1.1 |  | varint | 2 | 7% | 2 | 8657353…8657354 | 8657354 | poucas amostras | coordenada? (lat ou lon) zigzag/1e6 = -4.32868..4.32868 |
| 7.1.1 |  | varint | 42 | 50% | 6 | 5968777…8657354 | 8657354 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.32868..4.32868 |
| 7.1.3 |  | f32 | 42 | 50% | 6 | 51.67…66.656 | 51.67 | estado (poucos valores) | 0-100: percentual ou temperatura? |
| 7.1.4 |  | f32 | 42 | 50% | 6 | 51.67…66.656 | 51.67 | estado (poucos valores) | 0-100: percentual ou temperatura? |

### `20401_142004` — Bateria (info básica)

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 16 | 100% | 16 | 1678894515382…1678894530401 | 1678894530401 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 16 | 100% | 1 | — | 1377157 | constante | coordenada? (lat ou lon) zigzag/1e6 = -0.68858..-0.68858 |
| 5.1 |  | varint | 16 | 100% | 1 | — | 13 | constante | **Nº de células da bateria** (média) = 13 |
| 5.2 |  | varint | 16 | 100% | 1 | — | 4294967283 | constante | **Sensor da bateria (bruto)** (baixa) = -13 — talvez temperatura; inteiro negativo em 32 bits? (int32 =-13) |
| 5.4 |  | f32 | 16 | 100% | 16 | 1793.7…1808.7 | 1808.7 | contador/tempo | **Contador da bateria** (baixa) = 1808.7 |

### `20501_142004` — GPS / posição

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 309 | 100% | 64+ | 1678894514963…1678894531387 | 1678894531387 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 309 | 100% | 1 | — | 7 | constante |  |
| 4.2 |  | f32 | 62 | 20% | 1 | — | 1.1847 | constante |  |
| 4.3 |  | varint | 62 | 20% | 1 | — | 1 | constante |  |
| 6.1.1 |  | varint | 741 | 80% | 12 | 806156435…806156461 | 806156435 | variável lenta | **Longitude** (alta) = -40.308°; longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 6.1.2 |  | varint | 741 | 80% | 25 | 406572745…406572793 | 406572793 | variável lenta | **Latitude** (alta) = -20.329°; latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |

### `20602_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 82 | 100% | 64+ | 1469478079392…1469478095751 | 1469478095751 | contador/tempo | inteiro negativo em 32 bits? (int32 =599280519) |
| 2 |  | varint | 82 | 100% | 1 | — | 8 | constante |  |
| 4.1.1 |  | u64 | 82 | 100% | 64+ | 1794633531200…1794633547600 | 1794633547600 | contador/tempo | fixed inteiro (bits de status?) |
| 4.1.6 |  | varint | 82 | 100% | 14 | 806156435…806156461 | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 4.1.7 |  | varint | 82 | 100% | 24 | 406572747…406572793 | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 4.1.8 |  | varint | 82 | 100% | 1 | — | 89 | constante |  |
| 4.1.9 |  | varint | 82 | 100% | 1 | — | 17 | constante |  |
| 4.1.10 |  | varint | 82 | 100% | 2 | 156…158 | 158 | estado (poucos valores) |  |
| 4.1.11 |  | varint | 82 | 100% | 17 | 1570…4712 | 3140 | variável contínua |  |

### `20602_TO_IPC_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 325 | 100% | 64+ | 1469478079382…1469478095741 | 1469478095741 | contador/tempo | inteiro negativo em 32 bits? (int32 =599280509) |
| 2 |  | varint | 325 | 100% | 1 | — | 8 | constante |  |
| 4.1.1 |  | u64 | 325 | 100% | 64+ | 1794633531200…1794633547600 | 1794633547600 | variável contínua | fixed inteiro (bits de status?) |
| 4.1.6 |  | varint | 325 | 100% | 14 | 806156435…806156461 | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 4.1.7 |  | varint | 325 | 100% | 24 | 406572747…406572793 | 406572793 | variável lenta | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 4.1.8 |  | varint | 325 | 100% | 1 | — | 89 | constante |  |
| 4.1.9 |  | varint | 325 | 100% | 1 | — | 17 | constante |  |
| 4.1.10 |  | varint | 325 | 100% | 2 | 156…158 | 158 | estado (poucos valores) |  |
| 4.1.11 |  | varint | 325 | 100% | 18 | 1570…4712 | 3140 | variável lenta |  |

### `2202_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 7 | 100% | 7 | 1469478079684…1469478091037 | 1469478091037 | estado (poucos valores) | inteiro negativo em 32 bits? (int32 =599275805) |
| 2 |  | varint | 7 | 100% | 1 | — | 8 | constante |  |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968777 | str | 1 | 14% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968777 (por partes) |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968778 | str | 2 | 29% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968778 (por partes) |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968779 | str | 2 | 29% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968779 (por partes) |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968780 | str | 2 | 29% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968780 (por partes) |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968777 | str | 1 | 14% | 1 | — | '800' | poucas amostras |  |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968778 | str | 2 | 29% | 1 | — | '800' | poucas amostras |  |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968779 | str | 2 | 29% | 1 | — | '800' | poucas amostras |  |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968780 | str | 2 | 29% | 1 | — | '800' | poucas amostras |  |

### `2203_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 2 |  | varint | 2 | 100% | 1 | — | 9 | poucas amostras |  |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968777 | str | 2 | 100% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968777 (por partes) |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968778 | str | 2 | 100% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968778 (por partes) |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968779 | str | 2 | 100% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968779 (por partes) |
| 5.1.1 | motion_ctrl.actuators:cmd_limit:5968780 | str | 2 | 100% | 1 | — | 'motion_ctrl.actuators:cmd_…' | poucas amostras | ≈ motion controle actuators comando limit 5968780 (por partes) |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968777 | str | 2 | 100% | 1 | — | '800' | poucas amostras |  |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968778 | str | 2 | 100% | 1 | — | '800' | poucas amostras |  |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968779 | str | 2 | 100% | 1 | — | '800' | poucas amostras |  |
| 5.1.2 | motion_ctrl.actuators:cmd_limit:5968780 | str | 2 | 100% | 1 | — | '800' | poucas amostras |  |

### `25101_142004` — Radar (alvos)

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 114 | 100% | 64+ | 1678894515044…1678894531262 | 1678894531262 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 114 | 100% | 1 | — | 7 | constante |  |
| 4.1.1 |  | varint | 16 | 14% | 1 | — | 1 | constante |  |
| 4.1.2.1.1 |  | varint | 423 | 28% | 1 | — | 806156945 | constante | longitude? zigzag/1e7 = -40.30785..-40.30785 (perto da região do barco) |
| 4.1.2.1.2 |  | varint | 423 | 28% | 1 | — | 406573007 | constante | latitude? zigzag/1e7 = -20.32865..-20.32865 (perto da região do barco) |
| 4.1.2.2.1 |  | varint | 42540 | 28% | 64+ | 79…31920 | 31919 | variável contínua |  |
| 4.1.2.2.2 |  | varint | 42583 | 28% | 64+ | 79…31919 | 31839 | variável contínua |  |
| 5.1.1 | bs_72 | u64 | 82 | 72% | 17 | 1678894514725…1678894530720 | 1678894530720 | variável lenta | fixed inteiro (bits de status?) |
| 5.1.1 | radar_0 | u64 | 82 | 72% | 2 | 1678894514645…1678894524855 | 1678894524855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_134 | u64 | 82 | 72% | 3 | 1678894514646…1678894529857 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_150 | u64 | 82 | 72% | 7 | 1678894514640…1678894529855 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_2 | u64 | 82 | 72% | 7 | 1678894514647…1678894529858 | 1678894529858 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_22 | u64 | 82 | 72% | 64+ | 1678894515037…1678894531256 | 1678894531256 | variável contínua | fixed inteiro (bits de status?) |
| 5.1.1 | radar_35 | u64 | 82 | 72% | 7 | 1678894514651…1678894529860 | 1678894529860 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_378 | u64 | 82 | 72% | 3 | 1678894509431…1678894529856 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_436 | u64 | 82 | 72% | 4 | 1678894514641…1678894522250 | 1678894522250 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_457 | u64 | 82 | 72% | 1 | — | 1678894507031 | constante | fixed inteiro (bits de status?) |
| 5.1.1 | radar_458 | u64 | 82 | 72% | 7 | 1678894512045…1678894529859 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_5 | u64 | 82 | 72% | 7 | 1678894514642…1678894529856 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_537 | u64 | 82 | 72% | 7 | 1678894514638…1678894529855 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_576 | u64 | 82 | 72% | 4 | 1678894514648…1678894529537 | 1678894529537 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_6 | u64 | 82 | 72% | 7 | 1678894514643…1678894529857 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_626 | u64 | 82 | 72% | 6 | 1678894512044…1678894529859 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.1 | radar_640 | u64 | 63 | 55% | 3 | 1678894517254…1678894529861 | 1678894529861 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.2 | bs_72 | str | 82 | 72% | 1 | — | 'bs_72' | texto (constante) | **Nome do alvo de radar** (alta) = 'bs_72' |
| 5.1.2 | radar_0 | str | 82 | 72% | 1 | — | 'radar_0' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_0'; ≈ radar 0 (por partes) |
| 5.1.2 | radar_134 | str | 82 | 72% | 1 | — | 'radar_134' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_134'; ≈ radar 134 (por partes) |
| 5.1.2 | radar_150 | str | 82 | 72% | 1 | — | 'radar_150' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_150'; ≈ radar 150 (por partes) |
| 5.1.2 | radar_2 | str | 82 | 72% | 1 | — | 'radar_2' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_2'; ≈ radar 2 (por partes) |
| 5.1.2 | radar_22 | str | 82 | 72% | 1 | — | 'radar_22' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_22'; ≈ radar 22 (por partes) |
| 5.1.2 | radar_35 | str | 82 | 72% | 1 | — | 'radar_35' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_35'; ≈ radar 35 (por partes) |
| 5.1.2 | radar_378 | str | 82 | 72% | 1 | — | 'radar_378' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_378'; ≈ radar 378 (por partes) |
| 5.1.2 | radar_436 | str | 82 | 72% | 1 | — | 'radar_436' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_436'; ≈ radar 436 (por partes) |
| 5.1.2 | radar_457 | str | 82 | 72% | 1 | — | 'radar_457' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_457'; ≈ radar 457 (por partes) |
| 5.1.2 | radar_458 | str | 82 | 72% | 1 | — | 'radar_458' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_458'; ≈ radar 458 (por partes) |
| 5.1.2 | radar_5 | str | 82 | 72% | 1 | — | 'radar_5' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_5'; ≈ radar 5 (por partes) |
| 5.1.2 | radar_537 | str | 82 | 72% | 1 | — | 'radar_537' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_537'; ≈ radar 537 (por partes) |
| 5.1.2 | radar_576 | str | 82 | 72% | 1 | — | 'radar_576' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_576'; ≈ radar 576 (por partes) |
| 5.1.2 | radar_6 | str | 82 | 72% | 1 | — | 'radar_6' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_6'; ≈ radar 6 (por partes) |
| 5.1.2 | radar_626 | str | 82 | 72% | 1 | — | 'radar_626' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_626'; ≈ radar 626 (por partes) |
| 5.1.2 | radar_640 | str | 63 | 55% | 1 | — | 'radar_640' | texto (constante) | **Nome do alvo de radar** (alta) = 'radar_640'; ≈ radar 640 (por partes) |
| 5.1.4.1 | bs_72 | u64 | 82 | 72% | 17 | 1678894514725…1678894530720 | 1678894530720 | variável lenta | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_0 | u64 | 82 | 72% | 2 | 1678894514645…1678894524855 | 1678894524855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_134 | u64 | 82 | 72% | 3 | 1678894514646…1678894529857 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_150 | u64 | 82 | 72% | 7 | 1678894514640…1678894529855 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_2 | u64 | 82 | 72% | 7 | 1678894514647…1678894529858 | 1678894529858 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_22 | u64 | 82 | 72% | 64+ | 1678894515037…1678894531256 | 1678894531256 | variável contínua | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_35 | u64 | 82 | 72% | 7 | 1678894514651…1678894529860 | 1678894529860 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_378 | u64 | 82 | 72% | 3 | 1678894509431…1678894529856 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_436 | u64 | 82 | 72% | 4 | 1678894514641…1678894522250 | 1678894522250 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_457 | u64 | 82 | 72% | 1 | — | 1678894507031 | constante | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_458 | u64 | 82 | 72% | 7 | 1678894512045…1678894529859 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_5 | u64 | 82 | 72% | 7 | 1678894514642…1678894529856 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_537 | u64 | 82 | 72% | 7 | 1678894514638…1678894529855 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_576 | u64 | 82 | 72% | 4 | 1678894514648…1678894529537 | 1678894529537 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_6 | u64 | 82 | 72% | 7 | 1678894514643…1678894529857 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_626 | u64 | 82 | 72% | 6 | 1678894512044…1678894529859 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.1 | radar_640 | u64 | 63 | 55% | 3 | 1678894517254…1678894529861 | 1678894529861 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 5.1.4.6 | bs_72 | varint | 82 | 72% | 1 | — | 2268612680 | constante | coordenada? (lat ou lon) zigzag/1e7 = 113.43063..113.43063 |
| 5.1.4.6 | radar_0 | varint | 82 | 72% | 2 | 806268023…806268979 | 806268023 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31345..-40.31340 (perto da região do barco) |
| 5.1.4.6 | radar_134 | varint | 82 | 72% | 2 | 806152539…806152731 | 806152539 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30764..-40.30763 (perto da região do barco) |
| 5.1.4.6 | radar_150 | varint | 82 | 72% | 5 | 806147559…806148899 | 806147559 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30745..-40.30738 (perto da região do barco) |
| 5.1.4.6 | radar_2 | varint | 82 | 72% | 1 | — | 806162881 | constante | longitude? zigzag/1e7 = -40.30814..-40.30814 (perto da região do barco) |
| 5.1.4.6 | radar_22 | varint | 82 | 72% | 64+ | 806203305…806211867 | 806206277 | variável contínua | longitude? zigzag/1e7 = -40.31059..-40.31017 (perto da região do barco) |
| 5.1.4.6 | radar_35 | varint | 82 | 72% | 6 | 806160775…806162115 | 806160965 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30811..-40.30804 (perto da região do barco) |
| 5.1.4.6 | radar_378 | varint | 82 | 72% | 3 | 806220335…806221101 | 806220335 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31106..-40.31102 (perto da região do barco) |
| 5.1.4.6 | radar_436 | varint | 82 | 72% | 3 | 806222827…806223401 | 806223401 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31117..-40.31114 (perto da região do barco) |
| 5.1.4.6 | radar_457 | varint | 82 | 72% | 1 | — | 806167095 | constante | longitude? zigzag/1e7 = -40.30835..-40.30835 (perto da região do barco) |
| 5.1.4.6 | radar_458 | varint | 82 | 72% | 5 | 806171691…806174947 | 806173223 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30875..-40.30858 (perto da região do barco) |
| 5.1.4.6 | radar_5 | varint | 82 | 72% | 2 | 806198887…806199079 | 806199079 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30995..-40.30994 (perto da região do barco) |
| 5.1.4.6 | radar_537 | varint | 82 | 72% | 3 | 806154837…806155987 | 806155987 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30780..-40.30774 (perto da região do barco) |
| 5.1.4.6 | radar_576 | varint | 82 | 72% | 4 | 806205801…806210187 | 806205801 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31051..-40.31029 (perto da região do barco) |
| 5.1.4.6 | radar_6 | varint | 82 | 72% | 2 | 806297137…806297327 | 806297137 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31487..-40.31486 (perto da região do barco) |
| 5.1.4.6 | radar_626 | varint | 82 | 72% | 2 | 806210951…806211143 | 806210951 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31056..-40.31055 (perto da região do barco) |
| 5.1.4.6 | radar_640 | varint | 63 | 55% | 2 | 806178203…806180693 | 806180693 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30903..-40.30891 (perto da região do barco) |
| 5.1.4.7 | bs_72 | varint | 82 | 72% | 1 | — | 436103520 | constante | coordenada? (lat ou lon) zigzag/1e7 = 21.80518..21.80518 |
| 5.1.4.7 | radar_0 | varint | 82 | 72% | 2 | 406493155…406493335 | 406493335 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32467..-20.32466 (perto da região do barco) |
| 5.1.4.7 | radar_134 | varint | 82 | 72% | 2 | 406635513…406636777 | 406635513 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33184..-20.33178 (perto da região do barco) |
| 5.1.4.7 | radar_150 | varint | 82 | 72% | 7 | 406664597…406666947 | 406665863 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33335..-20.33323 (perto da região do barco) |
| 5.1.4.7 | radar_2 | varint | 82 | 72% | 2 | 406571561…406571741 | 406571561 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32859..-20.32858 (perto da região do barco) |
| 5.1.4.7 | radar_22 | varint | 82 | 72% | 64+ | 406659515…406672193 | 406672193 | variável contínua | latitude? zigzag/1e7 = -20.33361..-20.33298 (perto da região do barco) |
| 5.1.4.7 | radar_35 | varint | 82 | 72% | 3 | 406506345…406506887 | 406506705 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32534..-20.32532 (perto da região do barco) |
| 5.1.4.7 | radar_378 | varint | 82 | 72% | 2 | 406507247…406507969 | 406507969 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32540..-20.32536 (perto da região do barco) |
| 5.1.4.7 | radar_436 | varint | 82 | 72% | 4 | 406544643…406546269 | 406544643 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32731..-20.32723 (perto da região do barco) |
| 5.1.4.7 | radar_457 | varint | 82 | 72% | 1 | — | 406670199 | constante | latitude? zigzag/1e7 = -20.33351..-20.33351 (perto da região do barco) |
| 5.1.4.7 | radar_458 | varint | 82 | 72% | 5 | 406561445…406563431 | 406562709 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32817..-20.32807 (perto da região do barco) |
| 5.1.4.7 | radar_5 | varint | 82 | 72% | 1 | — | 406574631 | constante | latitude? zigzag/1e7 = -20.32873..-20.32873 (perto da região do barco) |
| 5.1.4.7 | radar_537 | varint | 82 | 72% | 6 | 406582943…406585109 | 406583123 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32926..-20.32915 (perto da região do barco) |
| 5.1.4.7 | radar_576 | varint | 82 | 72% | 3 | 406668391…406669295 | 406668601 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33346..-20.33342 (perto da região do barco) |
| 5.1.4.7 | radar_6 | varint | 82 | 72% | 4 | 406581855…406582577 | 406581855 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32913..-20.32909 (perto da região do barco) |
| 5.1.4.7 | radar_626 | varint | 82 | 72% | 2 | 406530371…406530551 | 406530371 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32653..-20.32652 (perto da região do barco) |
| 5.1.4.7 | radar_640 | varint | 63 | 55% | 2 | 406643461…406644365 | 406644365 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33222..-20.33217 (perto da região do barco) |
| 5.1.4.10 | radar_22 | varint | 82 | 72% | 18 | 4777…6105 | 6105 | variável lenta | **Radar X (bruto)** (baixa) = 6105 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_0 | varint | 82 | 72% | 2 | 1170…5872 | 5872 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 5872 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_134 | varint | 82 | 72% | 3 | 1463…6205 | 1463 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 1463 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_150 | varint | 82 | 72% | 7 | 233…5204 | 5204 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 5204 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_2 | varint | 82 | 72% | 7 | 3058…5826 | 5072 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 5072 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_22 | varint | 82 | 72% | 18 | 4777…6105 | 6105 | variável lenta | **Radar Y (bruto)** (baixa) = 6105 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_35 | varint | 82 | 72% | 7 | 1765…3141 | 2966 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 2966 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_378 | varint | 82 | 72% | 3 | 1288…3692 | 1414 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 1414 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_436 | varint | 82 | 72% | 4 | 3026…3616 | 3026 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 3026 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_457 | varint | 82 | 72% | 1 | — | 1289 | constante | **Radar Y (bruto)** (baixa) = 1289 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_458 | varint | 82 | 72% | 7 | 1290…5233 | 2294 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 2294 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_5 | varint | 82 | 72% | 7 | 29…827 | 401 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 401 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_537 | varint | 82 | 72% | 7 | 869…5990 | 5132 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 5132 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_576 | varint | 82 | 72% | 4 | 385…5548 | 5548 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 5548 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_6 | varint | 82 | 72% | 7 | 78…3361 | 306 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 306 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_626 | varint | 82 | 72% | 6 | 1450…1800 | 1702 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 1702 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.11 | radar_640 | varint | 63 | 55% | 3 | 1628…3044 | 2682 | estado (poucos valores) | **Radar Y (bruto)** (baixa) = 2682 — formato incerto: veja o diagnóstico do radar |
| 5.1.4.12 | radar_22 | varint | 82 | 72% | 3 | 1000…1258 | 1000 | estado (poucos valores) |  |
| 5.1.6.2 | radar_22 | varint | 82 | 72% | 1 | — | 1 | constante |  |
| 5.1.6.3 | bs_72 | f32 | 82 | 72% | 1 | — | 1 | constante |  |
| 5.1.6.3 | radar_0 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_134 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_150 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_2 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_22 | f32 | 82 | 72% | 3 | 0.93212…0.9868 | 0.9868 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 5.1.6.3 | radar_35 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_378 | f32 | 82 | 72% | 2 | 0.01…0.01547 | 0.01 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 5.1.6.3 | radar_436 | f32 | 82 | 72% | 2 | 0.01…0.010367 | 0.01 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 5.1.6.3 | radar_457 | f32 | 82 | 72% | 1 | — | 0.012862 | constante |  |
| 5.1.6.3 | radar_458 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_5 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_537 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_576 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_6 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_626 | f32 | 82 | 72% | 1 | — | 0.01 | constante |  |
| 5.1.6.3 | radar_640 | f32 | 63 | 55% | 1 | — | 0.01 | constante |  |
| 5.1.6.4 | radar_22 | f32 | 82 | 72% | 1 | — | 400 | constante |  |
| 5.1.6.5 | radar_22 | f32 | 82 | 72% | 1 | — | 300 | constante |  |
| 5.1.6.6 | bs_72 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_0 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_134 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_150 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_2 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_22 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_35 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_378 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_436 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_457 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_458 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_5 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_537 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_576 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_6 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_626 | f32 | 82 | 72% | 1 | — | 4 | constante |  |
| 5.1.6.6 | radar_640 | f32 | 63 | 55% | 1 | — | 4 | constante |  |

### `40101_142004` — Status geral (~2 KB; SOC/combustível ainda não localizados)

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 412 | 100% | 64+ | 1678894514976…1678894531367 | 1678894531367 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 412 | 100% | 1 | — | 7 | constante |  |
| 4.1 |  | bytes | 412 | 100% | 64+ | — | '24475224f60801fd00eef41802…' | variável contínua |  |

### `40202_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 1 | 100% | 1 | — | 1469478089189 | poucas amostras | inteiro negativo em 32 bits? (int32 =599273957) |
| 2 |  | varint | 1 | 100% | 1 | — | 8 | poucas amostras |  |
| 4.1.1 |  | u64 | 1 | 100% | 1 | — | 1469478088587 | poucas amostras | fixed inteiro (bits de status?) |
| 4.1.2 |  | varint | 1 | 100% | 1 | — | 710007989 | poucas amostras | coordenada? (lat ou lon) zigzag/1e7 = -35.50040..-35.50040 |
| 4.1.6 |  | varint | 1 | 100% | 1 | — | 806273087 | poucas amostras | longitude? zigzag/1e7 = -40.31365..-40.31365 (perto da região do barco) |
| 4.1.7 |  | varint | 1 | 100% | 1 | — | 406411743 | poucas amostras | latitude? zigzag/1e7 = -20.32059..-20.32059 (perto da região do barco) |
| 4.1.10 |  | varint | 1 | 100% | 1 | — | 8898 | poucas amostras |  |

### `50001_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 17 | 100% | 17 | 1678894515011…1678894531249 | 1678894531249 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 17 | 100% | 1 | — | 7 | constante |  |
| 6.1 |  | bytes | 17 | 100% | 1 | — | '00000500000001000000390000…' | constante |  |

### `50002_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 95 | 100% | 64+ | 1469478079413…1469478095708 | 1469478095708 | variável contínua | inteiro negativo em 32 bits? (int32 =599280476) |
| 2 |  | varint | 95 | 100% | 1 | — | 8 | constante |  |
| 8.1.1 | air_info | str | 7 | 7% | 1 | — | 'air_info' | texto (constante) |  |
| 8.1.1 | lift_info | str | 55 | 58% | 1 | — | 'lift_info' | texto (constante) |  |
| 8.1.1 | search_light_info | str | 33 | 35% | 1 | — | 'search_light_info' | texto (constante) | ≈ search luz info (por partes) |
| 8.1.2 | air_info | str | 7 | 7% | 1 | — | '{\n\t"air_info" : \n\t{\n\…' | texto (constante) | ≈ air info param ventoinha gear 3 modo setting 0 temperature setting 20 sensor compressor atual 0 0 compressor velocidade 0 condensing temperature 28 0 evaporation temperature 26 799999237060547 indoor temperature 27 100000381469727 energia tensão 0 0 wind velocidade gear 0 estado alarme estado 0 compressor estado 0 cooing estado 0 ventoinha high velocidade estado 0 ventoinha low velocidade estado 0 ventoinha medium velocidade estado 0 ventoinha estado 0 four way estado 0 heating estado 0 high tensão switch estado 0 low tensão switch estado 0 machine estado 0 thermal protector estado 0 water bomba estado 0 alarme communication falha 0 compressor alarme 0 compressor high temperature 0 compressor overload alarme 0 condensing probe falha 0 evaporation probe falha 0 high pressão alarme 0 high tensão alarme 0 indoor heat exchanger high temperature alarme 0 indoor heat exchanger low temperature alarme 0 indoor probe falha 0 low pressão alarme 0 low tensão alarme 0 module high temperature alarme 0 sea heat exchanger high temperature alarme 0 sea heat exchanger low temperature alarme 0 (por partes) |
| 8.1.2 | lift_info | str | 55 | 58% | 2 | — | '{"lift_info":{"1":{"state"…' | texto (varia) | ≈ lift info 1 estado 4 deep 0 000000 0 estado 4 deep 0 000000 force use 0 (por partes) |
| 8.1.2 | search_light_info | str | 33 | 35% | 1 | — | '{"search_light_info":{"sea…' | texto (constante) | ≈ search luz info search luz estado 0 (por partes) |

### `50101_142004` — Propulsão e leme

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 66 | 57% | 64+ | 1678894514966…1678894531241 | 1678894531241 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 115 | 100% | 2 | 2360497…4326677 | 2360497 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -2.16334..-1.18025 |
| 4.1.1 |  | varint | 49 | 43% | 1 | — | 1 | constante |  |
| 4.2.2.1 |  | varint | 49 | 43% | 11 | 806156435…806156459 | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 4.2.2.2 |  | varint | 49 | 43% | 24 | 406572747…406572793 | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 4.2.3.1 |  | varint | 49 | 43% | 11 | 806156435…806156459 | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 4.2.3.2 |  | varint | 49 | 43% | 24 | 406572747…406572793 | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 4.2.4.1 |  | varint | 49 | 43% | 11 | 806156435…806156459 | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 4.2.4.2 |  | varint | 49 | 43% | 24 | 406572747…406572793 | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 4.3.2 |  | f32 | 10 | 9% | 1 | — | -0 | constante |  |
| 4.3.6 |  | f32 | 66 | 57% | 2 | 0.078…0.079 | 0.079 | estado (poucos valores) | **Leme (steer)** (média) = 0.079? — unidade não confirmada (graus?); fração 0-1 (×100 = percentual?) |
| 4.3.8 |  | u32 | 66 | 57% | 43 | 1.2586e-06…2980819515 | 884666324 | variável contínua | fixed inteiro (bits de status?) |
| 4.3.15 |  | varint | 10 | 9% | 1 | — | 5 | constante |  |
| 4.5.1 | steer | str | 66 | 57% | 1 | — | 'steer' | texto (constante) | ≈ leme (por partes) |
| 4.6.1 | prop | str | 66 | 57% | 1 | — | 'prop' | texto (constante) |  |
| 4.7.11.1 |  | varint | 264 | 57% | 4 | 5968777…5968780 | 5968779 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -2.98439..2.98439 |

### `51103_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 28 | 100% | 13 | 1469478079650…1794575928273 | 1794575928273 | variável contínua | inteiro negativo em 32 bits? (int32 =-720401455) |
| 2 |  | varint | 28 | 100% | 2 | 8…72 | 72 | estado (poucos valores) |  |
| 3 |  | varint | 28 | 100% | 1 | — | 7 | constante |  |
| 4.1 |  | varint | 24 | 86% | 3 | 1300…20300 | 1300 | estado (poucos valores) |  |
| 4.2 |  | varint | 28 | 100% | 4 | 4…9 | 5 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |

### `51301_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1 |  | varint | 8 | 100% | 8 | 1678894516314…1678894530326 | 1678894530326 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 2 |  | varint | 8 | 100% | 1 | — | 7 | constante |  |
| 4.1 |  | varint | 8 | 100% | 1 | — | 3001 | constante |  |

### `51302_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 2 |  | varint | 18 | 100% | 1 | — | 8 | constante |  |
| 5.1 | air close because no in water | str | 1 | 6% | 1 | — | 'air close because no in wa…' | poucas amostras |  |
| 6.1 |  | str | 1 | 6% | 1 | — | 'Average power 65.949997 le…' | poucas amostras | ≈ average energia 65 949997 less than 80 and start all generators (por partes) |
| 6.1 | Lower throttle 80% batt < 70% | str | 2 | 11% | 1 | — | 'Lower throttle 80% batt < …' | poucas amostras |  |
| 6.1 | left side not in the water | str | 3 | 17% | 1 | — | 'left side not in the water' | texto (constante) | ≈ esquerdo side not in the water (por partes) |
| 6.1 | right side not in the water | str | 3 | 17% | 1 | — | 'right side not in the wate…' | texto (constante) | ≈ direito side not in the water (por partes) |
| 7 |  | str | 8 | 44% | 1 | — | '\n*can not fire generator …' | texto (constante) |  |

### `avos_tf_tree_142004` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| 1.1.1 | radar_id | f64 | 164 | 34% | 64+ | 1.6789e+09…1.6789e+09 | 1.6789e+09 | contador/tempo |  |
| 1.1.1 | usv_enu_3d_id | f64 | 325 | 66% | 64+ | 1.6789e+09…1.6789e+09 | 1.6789e+09 | contador/tempo |  |
| 1.1.1 | usv_ned_id | f64 | 325 | 66% | 64+ | 1.6789e+09…1.6789e+09 | 1.6789e+09 | contador/tempo |  |
| 1.1.1 | usv_xy_2d_id | f64 | 325 | 66% | 64+ | 1.6789e+09…1.6789e+09 | 1.6789e+09 | contador/tempo |  |
| 1.1.1 | usv_xy_3d_id | f64 | 325 | 66% | 64+ | 1.6789e+09…1.6789e+09 | 1.6789e+09 | contador/tempo |  |
| 1.2 | radar_id | str | 164 | 34% | 1 | — | 'radar_id' | texto (constante) | ≈ radar id (por partes) |
| 1.2 | usv_enu_3d_id | str | 325 | 66% | 1 | — | 'usv_enu_3d_id' | texto (constante) |  |
| 1.2 | usv_ned_id | str | 325 | 66% | 1 | — | 'usv_ned_id' | texto (constante) |  |
| 1.2 | usv_xy_2d_id | str | 325 | 66% | 1 | — | 'usv_xy_2d_id' | texto (constante) |  |
| 1.2 | usv_xy_3d_id | str | 325 | 66% | 1 | — | 'usv_xy_3d_id' | texto (constante) |  |
| 1.3 | radar_id | str | 164 | 34% | 1 | — | 'usv_xy_2d_id' | texto (constante) |  |
| 1.3 | usv_enu_3d_id | str | 325 | 66% | 1 | — | 'usv_ned_id' | texto (constante) |  |
| 1.3 | usv_ned_id | str | 325 | 66% | 1 | — | 'world_ned_id' | texto (constante) |  |
| 1.3 | usv_xy_2d_id | str | 325 | 66% | 1 | — | 'usv_ned_id' | texto (constante) |  |
| 1.3 | usv_xy_3d_id | str | 325 | 66% | 1 | — | 'usv_ned_id' | texto (constante) |  |
| 1.4.1 | usv_enu_3d_id | f32 | 325 | 66% | 2 | 0.99896…0.99898 | 0.99896 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.4.1 | usv_xy_3d_id | f32 | 325 | 66% | 2 | -0.022305…-0.022303 | -0.022303 | estado (poucos valores) |  |
| 1.4.2 | usv_enu_3d_id | f32 | 325 | 66% | 2 | 0.038879…0.039378 | 0.039378 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.4.2 | usv_xy_3d_id | f32 | 325 | 66% | 2 | -0.0053838…-0.0053726 | -0.0053838 | estado (poucos valores) |  |
| 1.4.3 | usv_enu_3d_id | f32 | 325 | 66% | 2 | 0.0053726…0.0053838 | 0.0053838 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.4.3 | usv_xy_2d_id | f32 | 325 | 66% | 2 | 0.03899…0.03949 | 0.03949 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.4.3 | usv_xy_3d_id | f32 | 325 | 66% | 2 | 0.038879…0.039378 | 0.039378 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.4.4 | radar_id | f32 | 164 | 34% | 1 | — | 1 | constante |  |
| 1.4.4 | usv_enu_3d_id | f32 | 325 | 66% | 2 | 0.022303…0.022305 | 0.022303 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.4.4 | usv_ned_id | f32 | 325 | 66% | 1 | — | 1 | constante |  |
| 1.4.4 | usv_xy_2d_id | f32 | 325 | 66% | 2 | 0.99922…0.99924 | 0.99922 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.4.4 | usv_xy_3d_id | f32 | 325 | 66% | 2 | 0.99896…0.99898 | 0.99896 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 1.5.1 | radar_id | f64 | 164 | 34% | 1 | — | -1.5 | constante |  |

### `tcp:7` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| Version |  | json:str | 33 | 97% | 1 | — | 'V2.1.03__Jun 22 2025__16:3…' | constante |  |
| boot_count |  | json:int | 33 | 97% | 1 | — | 18 | constante |  |
| current_ele |  | json:float | 33 | 97% | 9 | -0.19…0.22 | -0.12 | variável contínua |  |
| current_pull |  | json:float | 33 | 97% | 1 | — | 0.45 | constante |  |
| current_work_event |  | json:int | 33 | 97% | 1 | — | 17 | constante |  |
| current_work_status |  | json:int | 33 | 97% | 1 | — | 0 | constante |  |
| dev_weight |  | json:int | 1 | 3% | 1 | — | 0 | poucas amostras |  |
| group_winch_acc_speed_ratio_for1 |  | json:float | 1 | 3% | 1 | — | 0.8 | poucas amostras |  |
| group_winch_acc_speed_ratio_for2 |  | json:float | 1 | 3% | 1 | — | 0.8 | poucas amostras |  |
| group_winch_acc_speed_ratio_res1 |  | json:float | 1 | 3% | 1 | — | 0.8 | poucas amostras |  |
| group_winch_acc_speed_ratio_res2 |  | json:float | 1 | 3% | 1 | — | 0.8 | poucas amostras |  |
| group_winch_turn_rate_value_for1 |  | json:float | 1 | 3% | 1 | — | 0.4 | poucas amostras |  |
| group_winch_turn_rate_value_for2 |  | json:float | 1 | 3% | 1 | — | 0.4 | poucas amostras |  |
| group_winch_turn_rate_value_res1 |  | json:float | 1 | 3% | 1 | — | 0.268 | poucas amostras |  |
| group_winch_turn_rate_value_res2 |  | json:float | 1 | 3% | 1 | — | 0.15 | poucas amostras |  |
| group_winch_turn_rope_length |  | json:float | 1 | 3% | 1 | — | 0.5 | poucas amostras |  |
| heart_signal |  | json:int | 33 | 97% | 33 | 221…253 | 253 | contador/tempo |  |
| home_position_captured |  | json:int | 33 | 97% | 1 | — | 0 | constante |  |
| ip_addr |  | json:str | 1 | 3% | 1 | — | '192.168.27.20' | poucas amostras |  |
| ip_port |  | json:int | 1 | 3% | 1 | — | 7 | poucas amostras |  |
| limit0 |  | json:int | 33 | 97% | 1 | — | 0 | constante |  |
| limit1 |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| limit2 |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| limit3 |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| limit4 |  | json:int | 33 | 97% | 1 | — | 0 | constante |  |
| limit5 |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| limit6 |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| limit7 |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| limit8 |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| limit_ele_value |  | json:int | 1 | 3% | 1 | — | 30 | poucas amostras |  |
| mac_addr |  | json:str | 1 | 3% | 1 | — | '9e:eb:5b:e8:89:a3' | poucas amostras |  |
| max_pluse_value |  | json:int | 1 | 3% | 1 | — | 83333 | poucas amostras |  |
| max_rope_len |  | json:int | 1 | 3% | 1 | — | 100 | poucas amostras |  |
| maxweight_ratio |  | json:int | 1 | 3% | 1 | — | 100 | poucas amostras |  |
| nsd_once_rope_len |  | json:float | 1 | 3% | 1 | — | 0.1 | poucas amostras |  |
| once_rope_len |  | json:float | 1 | 3% | 1 | — | 0.1 | poucas amostras |  |
| pull_rope_len |  | json:float | 33 | 97% | 2 | 1.1833…1.1837 | 1.1833 | estado (poucos valores) |  |
| pull_status |  | json:int | 33 | 97% | 1 | — | 0 | constante |  |
| remain_min_rope_len |  | json:int | 1 | 3% | 1 | — | 10 | poucas amostras |  |
| root |  | json:str | 34 | 100% | 2 | — | 'winch_system_status' | estado (poucos valores) |  |
| sensor_max_weight_smaple |  | json:int | 1 | 3% | 1 | — | 1000000 | poucas amostras |  |
| sensor_once_rope_len |  | json:float | 1 | 3% | 1 | — | 0.2526 | poucas amostras |  |
| stop_work_status |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| target_reached |  | json:int | 33 | 97% | 1 | — | 1 | constante |  |
| towfish_lock_error |  | json:int | 33 | 97% | 1 | — | 0 | constante |  |
| weightlessness_ratio |  | json:int | 1 | 3% | 1 | — | 0 | poucas amostras |  |
| winch_acc_speed_ratio |  | json:float | 1 | 3% | 1 | — | 0.8 | poucas amostras |  |
| winch_current_angle |  | json:int | 33 | 97% | 1 | — | 292 | constante |  |
| winch_position |  | json:int | 33 | 97% | 1 | — | -1 | constante |  |
| winch_rate |  | json:float | 33 | 97% | 1 | — | 20833 | constante |  |
| winch_turn_rate_value |  | json:float | 1 | 3% | 1 | — | 0.6 | poucas amostras |  |

### `tcp:8` — desconhecido

| Campo | Item | Tipo | Amostras | Presença | Distintos | Faixa | Último | Comportamento | Significado / dicas |
|---|---|---|---|---|---|---|---|---|---|
| Version |  | json:str | 34 | 92% | 1 | — | 'no fault' | constante |  |
| app_version |  | json:str | 34 | 92% | 1 | — | 'v1.2.3-20251114_1010' | constante |  |
| current_ele |  | json:float | 34 | 92% | 1 | — | 0 | constante |  |
| current_pull |  | json:float | 34 | 92% | 1 | — | -0 | constante |  |
| current_temp |  | json:float | 34 | 92% | 1 | — | 37.3 | constante |  |
| current_vol |  | json:float | 34 | 92% | 18 | 23.91…24.3 | 24.13 | variável contínua |  |
| current_work_status |  | json:int | 34 | 92% | 1 | — | 0 | constante |  |
| dev_weight |  | json:float | 3 | 8% | 1 | — | 19 | constante |  |
| gateway |  | json:str | 3 | 8% | 1 | — | '192.168.27.1' | constante |  |
| hard_version |  | json:str | 34 | 92% | 1 | — | 'v1.2.3' | constante |  |
| heart_signal |  | json:int | 34 | 92% | 22 | 2308…2329 | 2329 | variável contínua |  |
| ip_addr |  | json:str | 3 | 8% | 1 | — | '192.168.27.22' | constante |  |
| ip_port |  | json:int | 3 | 8% | 1 | — | 0 | constante |  |
| limit0 |  | json:bool | 34 | 92% | 1 | — | True | constante |  |
| limit1 |  | json:bool | 34 | 92% | 1 | — | False | constante |  |
| limit4 |  | json:int | 34 | 92% | 1 | — | 1 | constante |  |
| limit5 |  | json:int | 34 | 92% | 1 | — | 1 | constante |  |
| limit_ele_value |  | json:float | 3 | 8% | 1 | — | 12 | constante |  |
| mac_addr |  | json:str | 3 | 8% | 1 | — | '0' | constante |  |
| max_bus_vol |  | json:float | 3 | 8% | 1 | — | 28.5 | constante |  |
| max_pluse_value |  | json:int | 3 | 8% | 1 | — | 0 | constante |  |
| max_rope_len |  | json:float | 3 | 8% | 1 | — | 100 | constante |  |
| maxweight_ratio |  | json:float | 3 | 8% | 1 | — | 12 | constante |  |
| min_bus_vol |  | json:float | 3 | 8% | 1 | — | 15.5 | constante |  |
| once_rope_len |  | json:float | 3 | 8% | 1 | — | 4.8 | constante |  |
| pull_rope_len |  | json:float | 34 | 92% | 1 | — | 0.02 | constante |  |
| pull_status |  | json:int | 34 | 92% | 1 | — | 0 | constante |  |
| remain_min_rope_len |  | json:float | 3 | 8% | 1 | — | 0.05 | constante |  |
| root |  | json:str | 37 | 100% | 2 | — | 'winch_system_status' | estado (poucos valores) |  |
| rope_speed |  | json:float | 34 | 92% | 1 | — | 0 | constante |  |
| sensor_once_rope_len |  | json:int | 3 | 8% | 1 | — | 1 | constante |  |
| serial_number |  | json:str | 34 | 92% | 1 | — | '123456' | constante |  |
| stop_work_status |  | json:int | 34 | 92% | 1 | — | 0 | constante |  |
| sys_time |  | json:str | 34 | 92% | 18 | — | '2026-10-21 23:07:03' | variável contínua |  |
| warn |  | json:str | 34 | 92% | 1 | — | 'no fault' | constante |  |
| weightlessness_ratio |  | json:float | 3 | 8% | 1 | — | 0 | constante |  |
| winch_acc_speed_ratio |  | json:float | 3 | 8% | 1 | — | 1 | constante |  |
| winch_forward_rate_value |  | json:float | 3 | 8% | 1 | — | 0.15 | constante |  |
| winch_rate |  | json:float | 34 | 92% | 14 | -0.09…0.12 | 0.05 | variável contínua |  |
| winch_revesal_rate_value |  | json:float | 3 | 8% | 1 | — | 0.15 | constante |  |
| winch_turn_rate_value |  | json:float | 3 | 8% | 1 | — | 0.15 | constante |  |

## 8. Campos desconhecidos com pistas (candidatos)

| Tópico | Campo | Item | Último | Comportamento | Pista |
|---|---|---|---|---|---|
| 20501_142004 | 1 |  | 1678894531387 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 50101_142004 | 1 |  | 1678894531241 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 50101_142004 | 2 |  | 2360497 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -2.16334..-1.18025 |
| 50101_142004 | 4.3.8 |  | 884666324 | variável contínua | fixed inteiro (bits de status?) |
| 50101_142004 | 4.7.11.1 |  | 5968779 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -2.98439..2.98439 |
| 40101_142004 | 1 |  | 1678894531367 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 50001_142004 | 1 |  | 1678894531249 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 20602_TO_IPC_142004 | 1 |  | 1469478095741 | contador/tempo | inteiro negativo em 32 bits? (int32 =599280509) |
| 20602_TO_IPC_142004 | 4.1.1 |  | 1794633547600 | variável contínua | fixed inteiro (bits de status?) |
| 20602_TO_IPC_142004 | 4.1.6 |  | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 20602_TO_IPC_142004 | 4.1.7 |  | 406572793 | variável lenta | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| avos_tf_tree_142004 | 1.4.3 | usv_xy_2d_id | 0.03949 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| avos_tf_tree_142004 | 1.4.4 | usv_xy_2d_id | 0.99922 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| avos_tf_tree_142004 | 1.4.3 | usv_xy_3d_id | 0.039378 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| avos_tf_tree_142004 | 1.4.4 | usv_xy_3d_id | 0.99896 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| avos_tf_tree_142004 | 1.4.1 | usv_enu_3d_id | 0.99896 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| avos_tf_tree_142004 | 1.4.2 | usv_enu_3d_id | 0.039378 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| avos_tf_tree_142004 | 1.4.3 | usv_enu_3d_id | 0.0053838 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| avos_tf_tree_142004 | 1.4.4 | usv_enu_3d_id | 0.022303 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 20602_142004 | 1 |  | 1469478095751 | contador/tempo | inteiro negativo em 32 bits? (int32 =599280519) |
| 20602_142004 | 4.1.1 |  | 1794633547600 | contador/tempo | fixed inteiro (bits de status?) |
| 20602_142004 | 4.1.6 |  | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 20602_142004 | 4.1.7 |  | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 25101_142004 | 1 |  | 1678894531262 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 25101_142004 | 5.1.1 | radar_626 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_626 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_626 | 806210951 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31056..-40.31055 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_626 | 406530371 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32653..-20.32652 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_537 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_537 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_537 | 806155987 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30780..-40.30774 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_537 | 406583123 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32926..-20.32915 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_134 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_134 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_134 | 806152539 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30764..-40.30763 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_134 | 406635513 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33184..-20.33178 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_458 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_458 | 1678894529859 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_458 | 806173223 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30875..-40.30858 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_458 | 406562709 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32817..-20.32807 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_22 | 1678894531256 | variável contínua | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_22 | 1678894531256 | variável contínua | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_22 | 806206277 | variável contínua | longitude? zigzag/1e7 = -40.31059..-40.31017 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_22 | 406672193 | variável contínua | latitude? zigzag/1e7 = -20.33361..-20.33298 (perto da região do barco) |
| 25101_142004 | 5.1.6.3 | radar_22 | 0.9868 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 25101_142004 | 5.1.1 | radar_5 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_5 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_5 | 806199079 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30995..-40.30994 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_576 | 1678894529537 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_576 | 1678894529537 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_576 | 806205801 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31051..-40.31029 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_576 | 406668601 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33346..-20.33342 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_378 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_378 | 1678894529856 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_378 | 806220335 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31106..-40.31102 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_378 | 406507969 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32540..-20.32536 (perto da região do barco) |
| 25101_142004 | 5.1.6.3 | radar_378 | 0.01 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 25101_142004 | 5.1.1 | radar_2 | 1678894529858 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_2 | 1678894529858 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.7 | radar_2 | 406571561 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32859..-20.32858 (perto da região do barco) |
| 25101_142004 | 5.1.1 | bs_72 | 1678894530720 | variável lenta | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | bs_72 | 1678894530720 | variável lenta | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.1 | radar_0 | 1678894524855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_0 | 1678894524855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_0 | 806268023 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31345..-40.31340 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_0 | 406493335 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32467..-20.32466 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_6 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_6 | 1678894529857 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_6 | 806297137 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31487..-40.31486 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_6 | 406581855 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32913..-20.32909 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_436 | 1678894522250 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_436 | 1678894522250 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_436 | 806223401 | estado (poucos valores) | longitude? zigzag/1e7 = -40.31117..-40.31114 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_436 | 406544643 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32731..-20.32723 (perto da região do barco) |
| 25101_142004 | 5.1.6.3 | radar_436 | 0.01 | estado (poucos valores) | fração 0-1 (×100 = percentual?) |
| 25101_142004 | 5.1.1 | radar_150 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_150 | 1678894529855 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_150 | 806147559 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30745..-40.30738 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_150 | 406665863 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33335..-20.33323 (perto da região do barco) |
| 25101_142004 | 5.1.1 | radar_35 | 1678894529860 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_35 | 1678894529860 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_35 | 806160965 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30811..-40.30804 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_35 | 406506705 | estado (poucos valores) | latitude? zigzag/1e7 = -20.32534..-20.32532 (perto da região do barco) |
| 50002_142004 | 1 |  | 1469478095708 | variável contínua | inteiro negativo em 32 bits? (int32 =599280476) |
| 10102_142004 | 1 |  | 1469478095754 | variável contínua | inteiro negativo em 32 bits? (int32 =599280522) |
| 20202_142004 | 1 |  | 1469478095604 | variável contínua | inteiro negativo em 32 bits? (int32 =599280372) |
| 20202_142004 | 4.3.2.1 |  | 6952417 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60728..-3.44344 |
| 10102_142004 | 5.1.1 | 空调制冷开关 | 1469478095536 | contador/tempo | fixed inteiro (bits de status?) |
| 20202_142004 | 4.3.3.1 |  | 6952467 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60731..-3.44347 |
| 20202_142004 | 4.3.4.1 |  | 6952367 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60726..-3.44342 |
| 20202_142004 | 4.3.5.1 |  | 7149205 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -3.60737..-3.44353 |
| 50101_142004 | 4.2.2.1 |  | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 50101_142004 | 4.2.2.2 |  | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 50101_142004 | 4.2.3.1 |  | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 50101_142004 | 4.2.3.2 |  | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 50101_142004 | 4.2.4.1 |  | 806156435 | variável lenta | longitude? zigzag/1e7 = -40.30782..-40.30782 (perto da região do barco) |
| 50101_142004 | 4.2.4.2 |  | 406572793 | variável contínua | latitude? zigzag/1e7 = -20.32864..-20.32864 (perto da região do barco) |
| 10102_142004 | 5.1.1 | 液冷机制冷 | 1469478095754 | contador/tempo | fixed inteiro (bits de status?) |
| 51103_142004 | 1 |  | 1794575928273 | variável contínua | inteiro negativo em 32 bits? (int32 =-720401455) |
| 51103_142004 | 4.2 |  | 5 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |
| 2202_142004 | 1 |  | 1469478091037 | estado (poucos valores) | inteiro negativo em 32 bits? (int32 =599275805) |
| 20202_142004 | 4.1.1 |  | 8067429 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.06648..4.06648 |
| 20202_142004 | 4.8.1 |  | 8657353 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.32868..4.32868 |
| 20101_142004 | 1 |  | 1678894531402 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 20401_142004 | 1 |  | 1678894530401 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 10102_142004 | 5.1.1 | 任务载荷 | 1469478182690 | contador/tempo | fixed inteiro (bits de status?) |
| 20202_142004 | 4.9.1 |  | 8722919 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.36146..4.36146 |
| 10102_142004 | 5.1.1 | 左发电机上电 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 左发电机手动模式 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 左发电机点火 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 右发电机上电 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 右发电机手动模式 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 右发电机点火 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 发电机自主管理 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 重启船电 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 取消入水限制 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 智能限制功率 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 重启电池BMS | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 重启电子域 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 重启感知设备 | 1469478182699 | contador/tempo | fixed inteiro (bits de status?) |
| 20301_142004 | 1 |  | 1678894530616 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 20301_142004 | 4.1.1 |  | 10.65 | estado (poucos valores) | 0-100: percentual ou temperatura? |
| 20301_142004 | 7.1.1 |  | 8657354 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.32868..4.32868 |
| 20301_142004 | 7.1.3 |  | 51.67 | estado (poucos valores) | 0-100: percentual ou temperatura? |
| 20301_142004 | 7.1.4 |  | 51.67 | estado (poucos valores) | 0-100: percentual ou temperatura? |
| 20202_142004 | 4.2.1 |  | 8591868 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -4.29593..4.29593 |
| 20103_142004 | 1 |  | 1794575928396 | contador/tempo | timestamp (milissegundos desde 1970)? |
| 20103_142004 | 4.1.1 |  | 1794575928396 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 天线倒伏升 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 天线倒伏降 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | AIS静默模式 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | SVP电池 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 任务工控机1点动开关 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 舱内照明灯 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 舱外照明灯(甲板) | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 舱外照明灯(拖曳) | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | NUC ↑ light | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | NUC ↓ light | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | Masthead light | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | Anchor light | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | White stern light | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | Navigation light | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 左外侧推进器电源 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 左内侧推进器电源 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 右外侧推进器电源 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 右内侧推进器电源 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 空调冷水机上电 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 拖曳系统上电 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | SVP绞车上电 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 左片体舱底泵 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 右片体舱底泵 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | White | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 左抽右 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 右抽左 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 10102_142004 | 5.1.1 | 自动油平衡 | 1469478095163 | contador/tempo | fixed inteiro (bits de status?) |
| 20202_142004 | 4.10.1 |  | 5968877 | estado (poucos valores) | coordenada? (lat ou lon) zigzag/1e6 = -2.98444..2.98444 |
| 20202_142004 | 4.10.9 |  | 32 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |
| 20202_142004 | 4.10.10 |  | 34 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |
| 20202_142004 | 4.10.11 |  | 34 | estado (poucos valores) | pode ser percentual 0-100 (bateria/combustível?) |
| 20102_142004 | 1 |  | 1469478095213 | contador/tempo | inteiro negativo em 32 bits? (int32 =599279981) |
| 20201_142004 | 1 |  | 1678894530230 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 20201_142004 | 6.1.1 |  | 1678894530230 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 10101_142004 | 1 |  | 1678894530230 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 10101_142004 | 6.1.1 |  | 1678894530220 | variável contínua | fixed inteiro (bits de status?) |
| 10101_142004 | 6.1.2 |  | 4326681 | variável contínua | coordenada? (lat ou lon) zigzag/1e7 = -0.53432..0.40337 |
| 51301_142004 | 1 |  | 1678894530326 | estado (poucos valores) | timestamp (milissegundos desde 1970)? |
| 25101_142004 | 5.1.1 | radar_640 | 1678894529861 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.1 | radar_640 | 1678894529861 | estado (poucos valores) | fixed inteiro (bits de status?) |
| 25101_142004 | 5.1.4.6 | radar_640 | 806180693 | estado (poucos valores) | longitude? zigzag/1e7 = -40.30903..-40.30891 (perto da região do barco) |
| 25101_142004 | 5.1.4.7 | radar_640 | 406644365 | estado (poucos valores) | latitude? zigzag/1e7 = -20.33222..-20.33217 (perto da região do barco) |

## 9. O que falta decodificar

- Tópicos sem descrição no catálogo: `10101_142004`, `1202_142004`, `1301_142004`, `20101_142004`, `20102_142004`, `20103_142004`, `20201_142004`, `20202_142004`, `20301_142004`, `20602_142004`, `20602_TO_IPC_142004`, `2202_142004`, `2203_142004`, `40202_142004`, `50001_142004`, `50002_142004`, `51103_142004`, `51301_142004`, `51302_142004`, `avos_tf_tree_142004`
- Sem marcadores: rode o modo `live` e digite o que você faz no software original (ex.: `liguei luz de popa`).
- Estado bruto das luzes (valores de `5.*.5` no tópico 10102): confirmar ligando/desligando com marcadores.
- SOC, combustível, tensão, corrente e rpm: provavelmente no tópico 40101; use `--find`.

## 10. Guinchos (JSON)

### tcp:7

| Chave | Tradução | Tipo | Amostras | Distintos | Faixa | Último | Comportamento |
|---|---|---|---|---|---|---|---|
| Version | versão | json:str | 33 | 1 | — | 'V2.1.03__Jun 22 2025__16:36:43' | constante |
| boot_count | boot contador | json:int | 33 | 1 | 18…18 | 18 | constante |
| current_ele | Corrente | json:float | 33 | 9 | -0.19…0.22 | -0.12 | variável contínua |
| current_pull | Tração | json:float | 33 | 1 | 0.45…0.45 | 0.45 | constante |
| current_work_event | atual trabalho event | json:int | 33 | 1 | 17…17 | 17 | constante |
| current_work_status | Estado de trabalho | json:int | 33 | 1 | 0…0 | 0 | constante |
| dev_weight | — | json:int | 1 | 1 | 0…0 | 0 | poucas amostras |
| group_winch_acc_speed_ratio_for1 | group guincho acc velocidade ratio for 1 | json:float | 1 | 1 | 0.8…0.8 | 0.8 | poucas amostras |
| group_winch_acc_speed_ratio_for2 | group guincho acc velocidade ratio for 2 | json:float | 1 | 1 | 0.8…0.8 | 0.8 | poucas amostras |
| group_winch_acc_speed_ratio_res1 | group guincho acc velocidade ratio res 1 | json:float | 1 | 1 | 0.8…0.8 | 0.8 | poucas amostras |
| group_winch_acc_speed_ratio_res2 | group guincho acc velocidade ratio res 2 | json:float | 1 | 1 | 0.8…0.8 | 0.8 | poucas amostras |
| group_winch_turn_rate_value_for1 | group guincho turn taxa value for 1 | json:float | 1 | 1 | 0.4…0.4 | 0.4 | poucas amostras |
| group_winch_turn_rate_value_for2 | group guincho turn taxa value for 2 | json:float | 1 | 1 | 0.4…0.4 | 0.4 | poucas amostras |
| group_winch_turn_rate_value_res1 | group guincho turn taxa value res 1 | json:float | 1 | 1 | 0.268…0.268 | 0.268 | poucas amostras |
| group_winch_turn_rate_value_res2 | group guincho turn taxa value res 2 | json:float | 1 | 1 | 0.15…0.15 | 0.15 | poucas amostras |
| group_winch_turn_rope_length | group guincho turn cabo comprimento | json:float | 1 | 1 | 0.5…0.5 | 0.5 | poucas amostras |
| heart_signal | — | json:int | 33 | 33 | 221…253 | 253 | contador/tempo |
| home_position_captured | — | json:int | 33 | 1 | 0…0 | 0 | constante |
| ip_addr | — | json:str | 1 | 1 | — | '192.168.27.20' | poucas amostras |
| ip_port | — | json:int | 1 | 1 | 7…7 | 7 | poucas amostras |
| limit0 | — | json:int | 33 | 1 | 0…0 | 0 | constante |
| limit1 | — | json:int | 33 | 1 | 1…1 | 1 | constante |
| limit2 | — | json:int | 33 | 1 | 1…1 | 1 | constante |
| limit3 | — | json:int | 33 | 1 | 1…1 | 1 | constante |
| limit4 | — | json:int | 33 | 1 | 0…0 | 0 | constante |
| limit5 | — | json:int | 33 | 1 | 1…1 | 1 | constante |
| limit6 | — | json:int | 33 | 1 | 1…1 | 1 | constante |
| limit7 | — | json:int | 33 | 1 | 1…1 | 1 | constante |
| limit8 | — | json:int | 33 | 1 | 1…1 | 1 | constante |
| limit_ele_value | limit corrente value | json:int | 1 | 1 | 30…30 | 30 | poucas amostras |
| mac_addr | — | json:str | 1 | 1 | — | '9e:eb:5b:e8:89:a3' | poucas amostras |
| max_pluse_value | máximo pluse value | json:int | 1 | 1 | 83333…83333 | 83333 | poucas amostras |
| max_rope_len | Cabo máximo | json:int | 1 | 1 | 100…100 | 100 | poucas amostras |
| maxweight_ratio | — | json:int | 1 | 1 | 100…100 | 100 | poucas amostras |
| nsd_once_rope_len | nsd once cabo comprimento | json:float | 1 | 1 | 0.1…0.1 | 0.1 | poucas amostras |
| once_rope_len | once cabo comprimento | json:float | 1 | 1 | 0.1…0.1 | 0.1 | poucas amostras |
| pull_rope_len | Cabo puxado | json:float | 33 | 2 | 1.1833…1.1837 | 1.1833 | estado (poucos valores) |
| pull_status | tração estado | json:int | 33 | 1 | 0…0 | 0 | constante |
| remain_min_rope_len | Cabo mínimo restante | json:int | 1 | 1 | 10…10 | 10 | poucas amostras |
| root | — | json:str | 34 | 2 | — | 'winch_system_status' | estado (poucos valores) |
| sensor_max_weight_smaple | sensor máximo weight smaple | json:int | 1 | 1 | 1000000…1000000 | 1000000 | poucas amostras |
| sensor_once_rope_len | sensor once cabo comprimento | json:float | 1 | 1 | 0.2526…0.2526 | 0.2526 | poucas amostras |
| stop_work_status | stop trabalho estado | json:int | 33 | 1 | 1…1 | 1 | constante |
| target_reached | alvo reached | json:int | 33 | 1 | 1…1 | 1 | constante |
| towfish_lock_error | towfish lock erro | json:int | 33 | 1 | 0…0 | 0 | constante |
| weightlessness_ratio | — | json:int | 1 | 1 | 0…0 | 0 | poucas amostras |
| winch_acc_speed_ratio | guincho acc velocidade ratio | json:float | 1 | 1 | 0.8…0.8 | 0.8 | poucas amostras |
| winch_current_angle | guincho atual ângulo | json:int | 33 | 1 | 292…292 | 292 | constante |
| winch_position | guincho position | json:int | 33 | 1 | -1…-1 | -1 | constante |
| winch_rate | Taxa do guincho | json:float | 33 | 1 | 20833…20833 | 20833 | constante |
| winch_turn_rate_value | guincho turn taxa value | json:float | 1 | 1 | 0.6…0.6 | 0.6 | poucas amostras |

### tcp:8

| Chave | Tradução | Tipo | Amostras | Distintos | Faixa | Último | Comportamento |
|---|---|---|---|---|---|---|---|
| Version | versão | json:str | 34 | 1 | — | 'no fault' | constante |
| app_version | app versão | json:str | 34 | 1 | — | 'v1.2.3-20251114_1010' | constante |
| current_ele | Corrente | json:float | 34 | 1 | 0…0 | 0 | constante |
| current_pull | Tração | json:float | 34 | 1 | -0…-0 | -0 | constante |
| current_temp | Temperatura | json:float | 34 | 1 | 37.3…37.3 | 37.3 | constante |
| current_vol | Tensão | json:float | 34 | 18 | 23.91…24.3 | 24.13 | variável contínua |
| current_work_status | Estado de trabalho | json:int | 34 | 1 | 0…0 | 0 | constante |
| dev_weight | — | json:float | 3 | 1 | 19…19 | 19 | constante |
| gateway | — | json:str | 3 | 1 | — | '192.168.27.1' | constante |
| hard_version | hard versão | json:str | 34 | 1 | — | 'v1.2.3' | constante |
| heart_signal | — | json:int | 34 | 22 | 2308…2329 | 2329 | variável contínua |
| ip_addr | — | json:str | 3 | 1 | — | '192.168.27.22' | constante |
| ip_port | — | json:int | 3 | 1 | 0…0 | 0 | constante |
| limit0 | — | json:bool | 34 | 1 | 1…1 | True | constante |
| limit1 | — | json:bool | 34 | 1 | 0…0 | False | constante |
| limit4 | — | json:int | 34 | 1 | 1…1 | 1 | constante |
| limit5 | — | json:int | 34 | 1 | 1…1 | 1 | constante |
| limit_ele_value | limit corrente value | json:float | 3 | 1 | 12…12 | 12 | constante |
| mac_addr | — | json:str | 3 | 1 | — | '0' | constante |
| max_bus_vol | máximo bus tensão | json:float | 3 | 1 | 28.5…28.5 | 28.5 | constante |
| max_pluse_value | máximo pluse value | json:int | 3 | 1 | 0…0 | 0 | constante |
| max_rope_len | Cabo máximo | json:float | 3 | 1 | 100…100 | 100 | constante |
| maxweight_ratio | — | json:float | 3 | 1 | 12…12 | 12 | constante |
| min_bus_vol | mínimo bus tensão | json:float | 3 | 1 | 15.5…15.5 | 15.5 | constante |
| once_rope_len | once cabo comprimento | json:float | 3 | 1 | 4.8…4.8 | 4.8 | constante |
| pull_rope_len | Cabo puxado | json:float | 34 | 1 | 0.02…0.02 | 0.02 | constante |
| pull_status | tração estado | json:int | 34 | 1 | 0…0 | 0 | constante |
| remain_min_rope_len | Cabo mínimo restante | json:float | 3 | 1 | 0.05…0.05 | 0.05 | constante |
| root | — | json:str | 37 | 2 | — | 'winch_system_status' | estado (poucos valores) |
| rope_speed | Velocidade do cabo | json:float | 34 | 1 | 0…0 | 0 | constante |
| sensor_once_rope_len | sensor once cabo comprimento | json:int | 3 | 1 | 1…1 | 1 | constante |
| serial_number | — | json:str | 34 | 1 | — | '123456' | constante |
| stop_work_status | stop trabalho estado | json:int | 34 | 1 | 0…0 | 0 | constante |
| sys_time | Hora do sistema | json:str | 34 | 18 | — | '2026-10-21 23:07:03' | variável contínua |
| warn | Alarme | json:str | 34 | 1 | — | 'no fault' | constante |
| weightlessness_ratio | — | json:float | 3 | 1 | 0…0 | 0 | constante |
| winch_acc_speed_ratio | guincho acc velocidade ratio | json:float | 3 | 1 | 1…1 | 1 | constante |
| winch_forward_rate_value | guincho forward taxa value | json:float | 3 | 1 | 0.15…0.15 | 0.15 | constante |
| winch_rate | Taxa do guincho | json:float | 34 | 14 | -0.09…0.12 | 0.05 | variável contínua |
| winch_revesal_rate_value | guincho revesal taxa value | json:float | 3 | 1 | 0.15…0.15 | 0.15 | constante |
| winch_turn_rate_value | guincho turn taxa value | json:float | 3 | 1 | 0.15…0.15 | 0.15 | constante |

## 11. Última mensagem de cada tópico (árvore)

### `10101_142004` (1203 B)

```
[1] varint 1678894530230   (zigzag=839447265115)
[2] varint 4982237   (zigzag=-2491119 → /1e7 = -0.249112)
[6] msg
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 2360497   (zigzag=-1180249 → /1e7 = -0.118025)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7017953   (zigzag=-3508977 → /1e7 = -0.350898)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 2360499   (zigzag=-1180250 → /1e7 = -0.118025)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7149205   (zigzag=-3574603 → /1e7 = -0.357460)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7083439   (zigzag=-3541720 → /1e7 = -0.354172)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7083539   (zigzag=-3541770 → /1e7 = -0.354177)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1377807   (zigzag=-688904)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1377808   (zigzag=688904)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1049177   (zigzag=-524589)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 6952597   (zigzag=-3476299 → /1e7 = -0.347630)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 6886831   (zigzag=-3443416 → /1e7 = -0.344342)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1049178   (zigzag=524589)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7149025   (zigzag=-3574513 → /1e7 = -0.357451)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 6886931   (zigzag=-3443466 → /1e7 = -0.344347)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1049277   (zigzag=-524639)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 8067429   (zigzag=-4033715 → /1e7 = -0.403371)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 8067430   (zigzag=4033715 → /1e7 = 0.403371)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 6952417   (zigzag=-3476209 → /1e7 = -0.347621)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7214511   (zigzag=-3607256 → /1e7 = -0.360726)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7214611   (zigzag=-3607306 → /1e7 = -0.360731)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1380357   (zigzag=-690179)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1377157   (zigzag=-688579)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7083669   (zigzag=-3541835 → /1e7 = -0.354183)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 1377159   (zigzag=-688580)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7017903   (zigzag=-3508952 → /1e7 = -0.350895)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7018003   (zigzag=-3509002 → /1e7 = -0.350900)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 6887061   (zigzag=-3443531 → /1e7 = -0.344353)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
    [1] u64 1678894530220 (0x186e5e97eac)
    [2] varint 7083489   (zigzag=-3541745 → /1e7 = -0.354175)
    [3] varint 8
    [4] varint 8
    [5] varint 2
    [11] bytes[1] 01
  [1] msg
… (truncado)
```

### `10102_142004` (45 B)

```
[1] varint 1469478095754   (zigzag=734739047877)
[2] varint 8
[5] msg
  [1] msg
    [1] u64 1469478095754 (0x15623b84b8a)
    [2] varint 65807   (zigzag=-32904)   ← ID do equipamento
    [3] str "液冷机制冷"   ← Nome do equipamento
    [5] varint 52   ← Estado bruto do equipamento
```

### `1202_142004` (8 B)

```
[2] varint 8
[3] varint 9
[6] msg
  [1] varint 2
```

### `1301_142004` (13 B)

```
[1] varint 1678894527397   (zigzag=-839447263699)
[2] varint 7
[4] msg
  [1] (vazio)
```

### `20101_142004` (13 B)

```
[1] varint 1678894531402   (zigzag=839447265701)
[2] varint 7
[5] msg
  [1] varint 4
```

### `20102_142004` (18 B)

```
[1] varint 1469478095213   (zigzag=-734739047607)
[2] varint 10686469   (zigzag=-5343235 → /1e7 = -0.534323)
[6] msg
  [1] varint 3
  [2] varint 4
```

### `20103_142004` (38 B)

```
[1] varint 1794575928396   (zigzag=897287964198)
[2] varint 72
[4] msg
  [1] msg
    [1] u64 1794575928396 (0x1a1d50f8c4c)
    [2] varint 72
    [6] varint 2268612680   (zigzag=1134306340 → /1e7 = 113.430634)
    [7] varint 436103520   (zigzag=218051760 → /1e7 = 21.805176)
  [2] varint 4
```

### `20201_142004` (34 B)

```
[1] varint 1678894530230   (zigzag=839447265115)
[2] varint 4982237   (zigzag=-2491119 → /1e7 = -0.249112)
[6] msg
  [1] msg
    [1] u64 1678894530230 (0x186e5e97eb6)
    [3] u64 101 (0x65)
```

### `20202_142004` (65 B)

```
[1] varint 1469478095604   (zigzag=734739047802)
[2] varint 8
[4] msg
  [3] msg
    [5] msg
      [1] varint 6887061   (zigzag=-3443531 → /1e7 = -0.344353)
  [3] msg
    [5] msg
      [1] varint 7214741   (zigzag=-3607371 → /1e7 = -0.360737)
  [3] msg
    [5] msg
      [1] varint 6952597   (zigzag=-3476299 → /1e7 = -0.347630)
  [3] msg
    [5] msg
      [1] varint 7018133   (zigzag=-3509067 → /1e7 = -0.350907)
  [3] msg
    [5] msg
      [1] varint 7083669   (zigzag=-3541835 → /1e7 = -0.354183)
  [3] msg
    [5] msg
      [1] varint 7149205   (zigzag=-3574603 → /1e7 = -0.357460)
```

### `20301_142004` (117 B)

```
[1] varint 1678894530616   (zigzag=839447265308)
[2] varint 657211   (zigzag=-328606)
[3] varint 72
[7] msg
  [1] msg
    [1] varint 5968777   (zigzag=-2984389 → /1e7 = -0.298439)
    [3] f32 66.4381
    [4] f32 66.4381
  [1] msg
    [1] varint 5968778   (zigzag=2984389 → /1e7 = 0.298439)
    [3] f32 66.6555
    [4] f32 66.6555
  [1] msg
    [1] varint 5968779   (zigzag=-2984390 → /1e7 = -0.298439)
    [3] f32 65.7906
    [4] f32 65.7906
  [1] msg
    [1] varint 5968780   (zigzag=2984390 → /1e7 = 0.298439)
    [3] f32 65.8467
    [4] f32 65.8467
  [1] msg
    [1] varint 8657353   (zigzag=-4328677 → /1e7 = -0.432868)
    [3] f32 54.7086
    [4] f32 54.7086
  [1] msg
    [1] varint 8657354   (zigzag=4328677 → /1e7 = 0.432868)
    [3] f32 51.67
    [4] f32 51.67
```

### `20401_142004` (26 B)

```
[1] varint 1678894530401   (zigzag=-839447265201)
[2] varint 1377157   (zigzag=-688579)
[5] msg
  [1] varint 13   ← Nº de células da bateria
  [2] varint 4294967283   (zigzag=-2147483642)   ← Sensor da bateria (bruto)
  [4] f32 1808.69   ← Contador da bateria
```

### `20501_142004` (53 B)

```
[1] varint 1678894531387   (zigzag=-839447265694)
[2] varint 7
[6] msg
  [1] msg
    [1] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)   ← Longitude
    [2] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)   ← Latitude
  [1] msg
    [1] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)   ← Longitude
    [2] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)   ← Latitude
  [1] msg
    [1] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)   ← Longitude
    [2] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)   ← Latitude
```

### `20602_142004` (48 B)

```
[1] varint 1469478095751   (zigzag=-734739047876)
[2] varint 8
[4] msg
  [1] msg
    [1] u64 1794633547600 (0x1a1d87ebf50)
    [6] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)
    [7] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)
    [8] varint 89
    [9] varint 17
    [10] varint 158   (zigzag=79)
    [11] varint 3140   (zigzag=1570)
  [2] (vazio)
  [3] (vazio)
```

### `20602_TO_IPC_142004` (48 B)

```
[1] varint 1469478095741   (zigzag=-734739047871)
[2] varint 8
[4] msg
  [1] msg
    [1] u64 1794633547600 (0x1a1d87ebf50)
    [6] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)
    [7] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)
    [8] varint 89
    [9] varint 17
    [10] varint 158   (zigzag=79)
    [11] varint 3140   (zigzag=1570)
  [2] (vazio)
  [3] (vazio)
```

### `2202_142004` (59 B)

```
[1] varint 1469478091037   (zigzag=-734739045519)
[2] varint 8
[5] msg
  [1] msg
    [1] str "motion_ctrl.actuators:cmd_limit:5968780"   → motion controle actuators comando limit 5968780 (≈ por partes)
    [2] str "800"
```

### `2203_142004` (197 B)

```
[2] varint 9
[5] msg
  [1] msg
    [1] str "motion_ctrl.actuators:cmd_limit:5968777"   → motion controle actuators comando limit 5968777 (≈ por partes)
    [2] str "800"
  [1] msg
    [1] str "motion_ctrl.actuators:cmd_limit:5968778"   → motion controle actuators comando limit 5968778 (≈ por partes)
    [2] str "800"
  [1] msg
    [1] str "motion_ctrl.actuators:cmd_limit:5968779"   → motion controle actuators comando limit 5968779 (≈ por partes)
    [2] str "800"
  [1] msg
    [1] str "motion_ctrl.actuators:cmd_limit:5968780"   → motion controle actuators comando limit 5968780 (≈ por partes)
    [2] str "800"
```

### `25101_142004` (1067 B)

```
[1] varint 1678894531262   (zigzag=839447265631)
[2] varint 7
[5] msg
  [1] msg
    [1] u64 1678894529859 (0x186e5e97d43)
    [2] str "radar_626"   → radar 626 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529859 (0x186e5e97d43)
      [6] varint 806210951   (zigzag=-403105476 → /1e7 = -40.310548)
      [7] varint 406530371   (zigzag=-203265186 → /1e7 = -20.326519)
      [11] varint 1702   (zigzag=851)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529855 (0x186e5e97d3f)
    [2] str "radar_537"   → radar 537 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529855 (0x186e5e97d3f)
      [6] varint 806155987   (zigzag=-403077994 → /1e7 = -40.307799)
      [7] varint 406583123   (zigzag=-203291562 → /1e7 = -20.329156)
      [11] varint 5132   (zigzag=2566)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529857 (0x186e5e97d41)
    [2] str "radar_134"   → radar 134 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529857 (0x186e5e97d41)
      [6] varint 806152539   (zigzag=-403076270 → /1e7 = -40.307627)
      [7] varint 406635513   (zigzag=-203317757 → /1e7 = -20.331776)
      [11] varint 1463   (zigzag=-732)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529861 (0x186e5e97d45)
    [2] str "radar_640"   → radar 640 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529861 (0x186e5e97d45)
      [6] varint 806180693   (zigzag=-403090347 → /1e7 = -40.309035)
      [7] varint 406644365   (zigzag=-203322183 → /1e7 = -20.332218)
      [11] varint 2682   (zigzag=1341)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529859 (0x186e5e97d43)
    [2] str "radar_458"   → radar 458 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529859 (0x186e5e97d43)
      [6] varint 806173223   (zigzag=-403086612 → /1e7 = -40.308661)
      [7] varint 406562709   (zigzag=-203281355 → /1e7 = -20.328135)
      [11] varint 2294   (zigzag=1147)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894531256 (0x186e5e982b8)
    [2] str "radar_22"   → radar 22 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894531256 (0x186e5e982b8)
      [6] varint 806206277   (zigzag=-403103139 → /1e7 = -40.310314)
      [7] varint 406672193   (zigzag=-203336097 → /1e7 = -20.333610)
      [10] varint 6105   (zigzag=-3053)   ← Radar X (bruto)
      [11] varint 6105   (zigzag=-3053)   ← Radar Y (bruto)
      [12] varint 1000   (zigzag=500)
    [6] msg
      [2] varint 1
      [3] f32 0.9868
      [4] f32 400
      [5] f32 300
      [6] f32 4
  [1] msg
    [1] u64 1678894529856 (0x186e5e97d40)
    [2] str "radar_5"   → radar 5 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529856 (0x186e5e97d40)
      [6] varint 806199079   (zigzag=-403099540 → /1e7 = -40.309954)
      [7] varint 406574631   (zigzag=-203287316 → /1e7 = -20.328732)
      [11] varint 401   (zigzag=-201)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529537 (0x186e5e97c01)
    [2] str "radar_576"   → radar 576 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529537 (0x186e5e97c01)
      [6] varint 806205801   (zigzag=-403102901 → /1e7 = -40.310290)
      [7] varint 406668601   (zigzag=-203334301 → /1e7 = -20.333430)
      [11] varint 5548   (zigzag=2774)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529856 (0x186e5e97d40)
    [2] str "radar_378"   → radar 378 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529856 (0x186e5e97d40)
      [6] varint 806220335   (zigzag=-403110168 → /1e7 = -40.311017)
      [7] varint 406507969   (zigzag=-203253985 → /1e7 = -20.325398)
      [11] varint 1414   (zigzag=707)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529858 (0x186e5e97d42)
    [2] str "radar_2"   → radar 2 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529858 (0x186e5e97d42)
      [6] varint 806162881   (zigzag=-403081441 → /1e7 = -40.308144)
      [7] varint 406571561   (zigzag=-203285781 → /1e7 = -20.328578)
      [11] varint 5072   (zigzag=2536)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894530720 (0x186e5e980a0)
    [2] str "bs_72"   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894530720 (0x186e5e980a0)
      [6] varint 2268612680   (zigzag=1134306340 → /1e7 = 113.430634)
      [7] varint 436103520   (zigzag=218051760 → /1e7 = 21.805176)
    [6] msg
      [3] f32 1
      [6] f32 4
  [1] msg
    [1] u64 1678894524855 (0x186e5e969b7)
    [2] str "radar_0"   → radar 0 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894524855 (0x186e5e969b7)
      [6] varint 806268023   (zigzag=-403134012 → /1e7 = -40.313401)
      [7] varint 406493335   (zigzag=-203246668 → /1e7 = -20.324667)
      [11] varint 5872   (zigzag=2936)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529857 (0x186e5e97d41)
    [2] str "radar_6"   → radar 6 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529857 (0x186e5e97d41)
      [6] varint 806297137   (zigzag=-403148569 → /1e7 = -40.314857)
      [7] varint 406581855   (zigzag=-203290928 → /1e7 = -20.329093)
      [11] varint 306   (zigzag=153)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894522250 (0x186e5e95f8a)
    [2] str "radar_436"   → radar 436 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894522250 (0x186e5e95f8a)
      [6] varint 806223401   (zigzag=-403111701 → /1e7 = -40.311170)
      [7] varint 406544643   (zigzag=-203272322 → /1e7 = -20.327232)
      [11] varint 3026   (zigzag=1513)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529855 (0x186e5e97d3f)
    [2] str "radar_150"   → radar 150 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529855 (0x186e5e97d3f)
      [6] varint 806147559   (zigzag=-403073780 → /1e7 = -40.307378)
      [7] varint 406665863   (zigzag=-203332932 → /1e7 = -20.333293)
      [11] varint 5204   (zigzag=2602)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
    [1] u64 1678894529860 (0x186e5e97d44)
    [2] str "radar_35"   → radar 35 (≈ por partes)   ← Nome do alvo de radar
    [3] (vazio)
    [4] msg
      [1] u64 1678894529860 (0x186e5e97d44)
      [6] varint 806160965   (zigzag=-403080483 → /1e7 = -40.308048)
      [7] varint 406506705   (zigzag=-203253353 → /1e7 = -20.325335)
      [11] varint 2966   (zigzag=1483)   ← Radar Y (bruto)
    [6] msg
      [3] f32 0.01
      [6] f32 4
  [1] msg
… (truncado)
```

### `40101_142004` (2309 B)

```
[1] varint 1678894531367   (zigzag=-839447265684)
[2] varint 7
[4] msg
  [1] bytes[2294] 24475224f60801fd00eef41802a00d0044af1506dc0beef002eef500ff00eeee…
```

### `40202_142004` (43 B)

```
[1] varint 1469478089189   (zigzag=-734739044595)
[2] varint 8
[4] msg
  [1] msg
    [1] u64 1469478088587 (0x15623b82f8b)
    [2] varint 710007989   (zigzag=-355003995 → /1e7 = -35.500400)
    [6] varint 806273087   (zigzag=-403136544 → /1e7 = -40.313654)
    [7] varint 406411743   (zigzag=-203205872 → /1e7 = -20.320587)
    [10] varint 8898   (zigzag=4449)
```

### `50001_142004` (71 B)

```
[1] varint 1678894531249   (zigzag=-839447265625)
[2] varint 7
[6] msg
  [1] bytes[58] 0000050000000100000039000000230000003700000001000000000000000000…
```

### `50002_142004` (81 B)

```
[1] varint 1469478095708   (zigzag=734739047854)
[2] varint 8
[8] msg
  [1] msg
    [1] str "search_light_info"   → search luz info (≈ por partes)
    [2] str "{"search_light_info":{"search_light_status":0}}"   → search luz info search luz estado 0 (≈ por partes)
```

### `50101_142004` (75 B)

```
[2] varint 2360497   (zigzag=-1180249 → /1e7 = -0.118025)
[4] msg
  [1] msg
    [1] varint 1
    [2] (vazio)
    [3] (vazio)
    [4] (vazio)
    [5] (vazio)
    [6] (vazio)
  [2] msg
    [2] msg
      [1] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)
      [2] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)
    [3] msg
      [1] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)
      [2] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)
    [4] msg
      [1] varint 806156435   (zigzag=-403078218 → /1e7 = -40.307822)
      [2] varint 406572793   (zigzag=-203286397 → /1e7 = -20.328640)
    [5] (vazio)
    [6] (vazio)
    [7] (vazio)
    [8] (vazio)
  [4] (vazio)
```

### `51103_142004` (18 B)

```
[1] varint 1794575928273   (zigzag=-897287964137)
[2] varint 72
[3] varint 7
[4] msg
  [1] varint 1300   (zigzag=650)
  [2] varint 5
```

### `51301_142004` (14 B)

```
[1] varint 1678894530326   (zigzag=839447265163)
[2] varint 7
[4] msg
  [1] varint 3001   (zigzag=-1501)
```

### `51302_142004` (35 B)

```
[2] varint 8
[6] msg
  [1] str "Lower throttle 80% batt < 70%"
```

### `avos_tf_tree_142004` (228 B)

```
[1] msg
  [1] msg
    [1] f64 1.67889e+09
  [2] str "usv_xy_2d_id"
  [3] str "usv_ned_id"
  [4] msg
    [3] f32 0.0394897
    [4] f32 0.99922
  [5] (vazio)
[1] msg
  [1] msg
    [1] f64 1.67889e+09
  [2] str "usv_xy_3d_id"
  [3] str "usv_ned_id"
  [4] msg
    [1] f32 -0.0223027
    [2] f32 -0.00538377
    [3] f32 0.0393782
    [4] f32 0.998961
  [5] (vazio)
[1] msg
  [1] msg
    [1] f64 1.67889e+09
  [2] str "usv_enu_3d_id"
  [3] str "usv_ned_id"
  [4] msg
    [1] f32 0.998961
    [2] f32 0.0393782
    [3] f32 0.00538377
    [4] f32 0.0223027
  [5] (vazio)
[1] msg
  [1] msg
    [1] f64 1.67889e+09
  [2] str "usv_ned_id"
  [3] str "world_ned_id"
  [4] msg
    [4] f32 1
  [5] (vazio)
```
