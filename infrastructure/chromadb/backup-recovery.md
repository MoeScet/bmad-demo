# ChromaDB Backup and Recovery Procedures

## Overview

This document outlines backup and recovery procedures for ChromaDB vector database deployed on Railway platform following BMAD infrastructure standards.

## Backup Strategy

### Automated Backups

ChromaDB data is persisted in Railway volumes with automatic snapshots:

- **Frequency**: Daily snapshots at 02:00 UTC
- **Retention**: 7 days for daily snapshots, 4 weeks for weekly snapshots
- **Location**: Railway managed volume snapshots
- **Monitoring**: Better Stack alerts if backup fails

### Manual Backup Procedures

#### 1. Export Collections via API

```bash
# Export all collections metadata
curl -X GET "https://bmad-chromadb-production.railway.app/api/v1/collections" \
  -H "Accept: application/json" > collections_backup.json

# Export specific collection data (requires custom script)
python scripts/backup_chromadb.py --collection-name bmad_embeddings --output-file embeddings_backup.json
```

#### 2. Volume Snapshot

```bash
# Create manual Railway volume snapshot
railway volume snapshot create --name "manual-backup-$(date +%Y%m%d)" --volume-id $CHROMA_VOLUME_ID
```

## Recovery Procedures

### Scenario 1: Service Restart (Data Intact)

1. **Identify Issue**
   ```bash
   railway logs --service bmad-chromadb-production
   ```

2. **Restart Service**
   ```bash
   railway service restart --service bmad-chromadb-production
   ```

3. **Verify Health**
   ```bash
   curl -f https://bmad-chromadb-production.railway.app/api/v1/heartbeat
   ```

**Recovery Time**: < 2 minutes

### Scenario 2: Data Corruption (Restore from Snapshot)

1. **Stop ChromaDB Service**
   ```bash
   railway service stop --service bmad-chromadb-production
   ```

2. **Restore Volume from Snapshot**
   ```bash
   railway volume restore --snapshot-id $SNAPSHOT_ID --volume-id $CHROMA_VOLUME_ID
   ```

3. **Start Service**
   ```bash
   railway service start --service bmad-chromadb-production
   ```

4. **Verify Collections**
   ```bash
   curl -X GET "https://bmad-chromadb-production.railway.app/api/v1/collections"
   ```

**Recovery Time**: < 5 minutes (meets coding standards <5 minute recovery time)

### Scenario 3: Complete Data Loss (Rebuild from Source)

1. **Create New Collection**
   ```bash
   python scripts/rebuild_chromadb.py --from-postgresql --collection-name bmad_embeddings
   ```

2. **Regenerate Embeddings**
   ```bash
   python scripts/regenerate_embeddings.py --source manual_content --batch-size 32
   ```

3. **Validate Collection**
   ```bash
   python scripts/validate_chromadb.py --collection-name bmad_embeddings
   ```

**Recovery Time**: 30-60 minutes (depending on data volume)

## Data Validation

### Health Check Validation

```bash
# Basic connectivity
curl -f https://bmad-chromadb-production.railway.app/api/v1/heartbeat

# Collection count validation
python scripts/validate_collection_counts.py --expected-min 1000
```

### Performance Validation

```bash
# Search performance test (<2 second requirement)
python scripts/performance_test.py --target-latency 2000 --queries 100
```

## Monitoring and Alerting

### Railway Health Checks

- **Endpoint**: `/api/v1/heartbeat`
- **Frequency**: Every 30 seconds
- **Timeout**: 10 seconds
- **Failure Threshold**: 3 consecutive failures

### Better Stack Integration

- **Uptime Monitoring**: ChromaDB health endpoint
- **Log Monitoring**: Error patterns in Railway logs
- **Performance Monitoring**: Response time alerts >2 seconds

### Alert Conditions

1. **Service Down**: 3+ consecutive health check failures
2. **High Latency**: Search queries >2 seconds for 5+ minutes
3. **Low Disk Space**: Volume usage >85%
4. **Memory Issues**: Container restart due to OOM

## Environment-Specific Configurations

### Production Environment

- **Service**: `bmad-chromadb-production`
- **Volume**: Persistent with daily snapshots
- **Resources**: 1GB RAM, 10GB storage
- **Backup Retention**: 4 weeks

### Staging Environment

- **Service**: `bmad-chromadb-staging`
- **Volume**: Persistent with weekly snapshots
- **Resources**: 512MB RAM, 5GB storage
- **Backup Retention**: 1 week

## Recovery Testing

### Monthly Recovery Drill

1. Create test collection in staging
2. Take manual snapshot
3. Simulate data corruption
4. Restore from snapshot
5. Validate data integrity
6. Document recovery time

### Performance Baseline

- **Search Latency**: < 500ms for 90% of queries
- **Collection Creation**: < 10 seconds
- **Embedding Generation**: < 100ms per document
- **Service Startup**: < 30 seconds

## Emergency Contacts

- **Primary**: DevOps Team (Better Stack alerts)
- **Secondary**: Engineering Lead
- **Railway Support**: For platform-specific issues

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Check Railway service status
   - Verify network connectivity
   - Review health check logs

2. **Slow Query Performance**
   - Check collection size vs available memory
   - Review indexing strategy
   - Monitor concurrent query load

3. **Storage Issues**
   - Monitor volume usage
   - Check for data growth patterns
   - Review embedding dimension efficiency

### Log Analysis

```bash
# Search for connection errors
railway logs --service bmad-chromadb-production | grep -i "connection"

# Check performance issues
railway logs --service bmad-chromadb-production | grep -i "timeout\|slow"

# Monitor resource usage
railway logs --service bmad-chromadb-production | grep -i "memory\|disk"
```