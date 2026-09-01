# Modelo estrela

## Dimensões
- dim_data
- dim_distribuidora
- dim_conjunto
- dim_indicador
- dim_tipo_interrupcao
- dim_motivo_interrupcao
- dim_fato_gerador

## Fatos
- fato_continuidade
- fato_interrupcao
- fato_causa_mensal

Não relacione fatos diretamente entre si. Use dimensões conformadas com cardinalidade 1:*.
