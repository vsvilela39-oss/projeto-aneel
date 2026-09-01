# Medidas DAX

```DAX
DEC Médio =
CALCULATE(
    AVERAGE(fato_continuidade[VlrIndicador]),
    dim_indicador[SigIndicador] = "DEC"
)
```

```DAX
FEC Médio =
CALCULATE(
    AVERAGE(fato_continuidade[VlrIndicador]),
    dim_indicador[SigIndicador] = "FEC"
)
```

```DAX
Transgressões =
CALCULATE(
    COUNTROWS(fato_continuidade),
    fato_continuidade[UltrapassouLimite] = 1
)
```

```DAX
Taxa de Transgressão % =
DIVIDE([Transgressões], COUNTROWS(fato_continuidade), 0)
```

```DAX
Qtd Interrupções = DISTINCTCOUNT(fato_interrupcao[InterrupcaoKey])
```

```DAX
Consumidor-Hora = SUM(fato_interrupcao[ConsumidorHoras])
```

```DAX
Contribuição DEC Estimada = SUM(fato_causa_mensal[ContribDEC_Estimada])
```

```DAX
Contribuição FEC Estimada = SUM(fato_causa_mensal[ContribFEC_Estimada])
```
