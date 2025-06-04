# Data API NB Test

Current 'standard' command line:

```
nb5 workload_thin.yaml astra_dapi_thin_write1 \
  astraToken=$ASTRA_DB_APPLICATION_TOKEN \
  astraApiEndpoint=$ASTRA_DB_API_ENDPOINT \
  namespace=$ASTRA_DB_KEYSPACE \
  cyclerate=30 rampup-cycles=100 rampup-threads=5 main-cycles=400 main-threads=10 \
  --progress console:2s --log-histograms 'histogram_hdr_data.log:.*.thin.*.result:4s'
```
