# FinOps live mode

El dominio `multicloud_mcp.finops` es una capa FOCUS-aligned para consultas live; no declara conformidad FOCUS ni implementa exports, CUR o datasets persistentes.

```text
MCP tool
  -> FinOpsQueryPlanner
  -> FinOpsCostService (cache corto + asyncio.gather)
  -> FinOpsProvider
       -> AWS Cost Explorer / Azure Cost Management Query API
  -> FinOpsCostResult normalizado
```

El modelo mínimo expone `ProviderName`, `SubAccountId`, `ServiceName`, `ServiceCategory`, `RegionId`, `BilledCost`, `EffectiveCost`, `Currency`, `StartDate` y `EndDate`. Los importes se representan con `Decimal` y las fechas usan inicio inclusivo/fin exclusivo.

AWS usa `NetAmortizedCost` con fallback a `AmortizedCost` para `effective_cost`, y `NetUnblendedCost` con fallback a `UnblendedCost` para `billed_cost`. Azure usa `AmortizedCost` y `ActualCost` respectivamente, agregando por `PreTaxCost`.

Las dimensiones `service`, `account` y `region` se envían al proveedor para agregación remota. `service_category` se normaliza localmente desde el nombre de servicio. Las consultas AWS/Azure se ejecutan concurrentemente y una falla parcial se devuelve marcada con `partial` y `providers_failed`.

Los tools P0 son `finops__get_cost`, `finops__breakdown` y `finops__compare`. No se convierten monedas ni se suman monedas diferentes; los resultados quedan separados por `Currency`.
