# S3 Integration Guide for Rayden Rules

## Overview

This guide explains how to configure AWS S3 storage for the Rayden Rules Kedro pipeline. S3 integration allows you to:
- Store bronze/silver/gold data in cloud storage
- Enable team collaboration with shared data
- Scale storage without local disk constraints
- Integrate with AWS analytics services

## Prerequisites

1. **AWS Account** with S3 access
2. **AWS CLI** installed and configured
3. **Boto3** Python library (already in requirements.txt)
4. **S3 Bucket** created for the project

## Setup Instructions

### Step 1: Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://raydenrules-data --region us-east-1

# Or use AWS Console: https://s3.console.aws.amazon.com/
```

### Step 2: Configure AWS Credentials

#### Option A: Using AWS CLI Profile

```bash
# Configure AWS CLI with your credentials
aws configure --profile raydenrules

# Enter your credentials when prompted:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1
# Default output format: json
```

#### Option B: Using Kedro Credentials File

Edit `conf/local/credentials.yml`:

```yaml
dev_s3:
  aws_access_key_id: YOUR_ACCESS_KEY
  aws_secret_access_key: YOUR_SECRET_KEY
  # Optional: if using temporary credentials
  aws_session_token: YOUR_SESSION_TOKEN

prod_s3:
  aws_access_key_id: YOUR_PROD_ACCESS_KEY
  aws_secret_access_key: YOUR_PROD_SECRET_KEY
```

**⚠️ Security Warning:** Never commit credentials to version control! The `conf/local/` directory should be in `.gitignore`.

### Step 3: Update Catalog for S3

Edit `conf/base/catalog_s3.yml` to point to your S3 bucket:

```yaml
# Bronze layer in S3
bronze_granules_partitioned:
  type: PartitionedDataset
  path: s3://raydenrules-data/bronze/granules
  dataset:
    type: pandas.ParquetDataset
    save_args:
      engine: pyarrow
      compression: snappy
    load_args:
      engine: pyarrow
  filename_suffix: .parquet
  credentials: dev_s3

bronze_granules_consolidated:
  type: pandas.ParquetDataset
  filepath: s3://raydenrules-data/bronze/granules_consolidated.parquet
  save_args:
    engine: pyarrow
    compression: snappy
  load_args:
    engine: pyarrow
  versioned: true
  credentials: dev_s3

# Add similar entries for other datasets...
```

### Step 4: Run Pipeline with S3

#### Using AWS Profile

```bash
# Set environment variable
export AWS_PROFILE=raydenrules

# Run pipeline
kedro run --pipeline=discovery_to_bronze
```

#### Using Kedro Environment

```bash
# Run with S3 catalog configuration
kedro run --pipeline=discovery_to_bronze --env=s3
```

## S3 Bucket Structure

Recommended S3 bucket organization (aligned with Kedro medallion architecture):

```
s3://raydenrules-data/
├── raw/                         # Raw API responses (01_raw)
│   └── cmr_discovery/
│       ├── NYC001_lst_data.json
│       ├── LAX001_lst_data.json
│       ├── CHI001_lst_data.json
│       └── MIA001_lst_data.json
├── intermediate/                # Bronze layer (02_intermediate)
│   ├── granules/                # Partitioned bronze granules
│   │   ├── NYC001.parquet
│   │   ├── LAX001.parquet
│   │   ├── CHI001.parquet
│   │   └── MIA001.parquet
│   ├── granules_consolidated.parquet/
│   │   └── 2025-10-30T12.00.00.000Z/
│   │       └── granules_consolidated.parquet
│   ├── manifest.parquet/
│   │   └── 2025-10-30T12.00.00.000Z/
│   │       └── manifest.parquet
│   ├── metadata.parquet/
│   │   └── 2025-10-30T12.00.00.000Z/
│   │       └── metadata.parquet
│   ├── metrics_prep/            # Ready for silver processing
│   │   ├── NYC001.parquet
│   │   └── ...
│   ├── cmr_discovery_results.json/
│   └── regions_list.json/
├── primary/                     # Silver layer - calculated metrics (03_primary)
│   └── metrics_by_region/       # Future
├── feature/                     # Silver layer - engineered features (04_feature)
│   └── enriched_metrics/        # Future
└── reporting/                   # Gold layer - aggregated KPIs (08_reporting)
    └── kpi_summary/             # Future
```

**Layer Mapping:**
- **Bronze = Intermediate** (`02_intermediate/`)
- **Silver = Primary + Feature** (`03_primary/`, `04_feature/`)
- **Gold = Reporting** (`08_reporting/`)

## IAM Permissions

Your AWS user/role needs these S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::raydenrules-data"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::raydenrules-data/*"
    }
  ]
}
```

## Testing S3 Connection

### Test AWS CLI Access

```bash
# List bucket contents
aws s3 ls s3://raydenrules-data/

# Copy test file
echo "test" > test.txt
aws s3 cp test.txt s3://raydenrules-data/test.txt

# Verify
aws s3 ls s3://raydenrules-data/test.txt

# Clean up
aws s3 rm s3://raydenrules-data/test.txt
rm test.txt
```

### Test Kedro S3 Integration

Create a test script `test_s3_connection.py`:

```python
import boto3
import pandas as pd
from kedro.io import DataCatalog
from kedro.io.data_catalog import DataCatalog
from kedro_datasets.pandas import ParquetDataset

# Test boto3 connection
s3 = boto3.client('s3')
response = s3.list_buckets()
print("Available buckets:", [b['Name'] for b in response['Buckets']])

# Test Kedro dataset
test_df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
dataset = ParquetDataset(
    filepath='s3://raydenrules-data/test/test_data.parquet',
    credentials={
        'aws_access_key_id': 'YOUR_KEY',
        'aws_secret_access_key': 'YOUR_SECRET'
    }
)
dataset.save(test_df)
print("Test data saved to S3!")

# Load back
loaded_df = dataset.load()
print("Test data loaded from S3:")
print(loaded_df)
```

Run the test:
```bash
python test_s3_connection.py
```

## Cost Optimization

### S3 Storage Costs

Typical costs for Rayden Rules data:
- **Standard Storage:** ~$0.023 per GB/month
- **PUT Requests:** $0.005 per 1,000 requests
- **GET Requests:** $0.0004 per 1,000 requests

**Example:** 10 GB of bronze data = ~$0.23/month

### Optimization Tips

1. **Use Parquet Compression**
   ```yaml
   save_args:
     compression: snappy  # Reduces storage by 50-80%
   ```

2. **Enable S3 Lifecycle Policies**
   ```bash
   # Move old versions to cheaper storage
   aws s3api put-bucket-lifecycle-configuration \
     --bucket raydenrules-data \
     --lifecycle-configuration file://lifecycle.json
   ```

   Example `lifecycle.json`:
   ```json
   {
     "Rules": [
       {
         "Id": "MoveOldVersions",
         "Status": "Enabled",
         "Transitions": [
           {
             "Days": 30,
             "StorageClass": "STANDARD_IA"
           },
           {
             "Days": 90,
             "StorageClass": "GLACIER"
           }
         ]
       }
     ]
   }
   ```

3. **Use S3 Intelligent-Tiering**
   ```bash
   aws s3api put-bucket-intelligent-tiering-configuration \
     --bucket raydenrules-data \
     --id RaydenRulesAutoTier \
     --intelligent-tiering-configuration file://tiering.json
   ```

## Hybrid Setup (Local + S3)

You can use S3 for some datasets and local for others:

In `conf/base/catalog.yml`:
```yaml
# Keep discovery results local (fast iteration)
cmr_discovery_results:
  type: json.JSONDataset
  filepath: data/02_intermediate/cmr_discovery_results.json
  versioned: true

# Store bronze in S3 (shared access)
bronze_granules_consolidated:
  type: pandas.ParquetDataset
  filepath: s3://raydenrules-data/bronze/granules_consolidated.parquet
  credentials: dev_s3
```

## Troubleshooting

### Error: "NoCredentialsError: Unable to locate credentials"

**Solutions:**
1. Check AWS CLI configuration: `aws configure list`
2. Verify credentials file: `cat ~/.aws/credentials`
3. Set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

### Error: "ClientError: An error occurred (403) when calling the PutObject operation: Forbidden"

**Solutions:**
1. Verify IAM permissions (see IAM Permissions section)
2. Check bucket policy doesn't deny access
3. Verify bucket region matches your configuration

### Error: "ParserError: Error tokenizing data"

**Solution:** This usually means S3 path doesn't exist. Create the bucket/prefix first:
```bash
aws s3api put-object --bucket raydenrules-data --key bronze/
```

### Slow Performance

**Solutions:**
1. Use S3 Transfer Acceleration:
   ```bash
   aws s3api put-bucket-accelerate-configuration \
     --bucket raydenrules-data \
     --accelerate-configuration Status=Enabled
   ```

2. Increase chunk size in catalog:
   ```yaml
   load_args:
     buffer_size: 10485760  # 10MB
   ```

3. Use same AWS region as S3 bucket

## Environment-Specific Configuration

Create different catalog files for each environment:

```
conf/
├── base/
│   └── catalog.yml          # Default (local)
├── local/
│   └── catalog.yml          # Local overrides
└── prod/
    └── catalog.yml          # Production (S3)
```

**`conf/prod/catalog.yml`:**
```yaml
# All datasets use S3 in production
_s3_base: &s3_base
  credentials: prod_s3

bronze_granules_consolidated:
  <<: *s3_base
  type: pandas.ParquetDataset
  filepath: s3://raydenrules-prod/bronze/granules_consolidated.parquet
```

Run with environment:
```bash
kedro run --env=prod
```

## Monitoring S3 Usage

### Check Storage Size

```bash
# Total bucket size
aws s3 ls s3://raydenrules-data/ --recursive --summarize | grep "Total Size"

# Size by prefix
aws s3 ls s3://raydenrules-data/bronze/ --recursive --summarize
```

### Enable S3 Metrics

```bash
# Enable request metrics
aws s3api put-bucket-metrics-configuration \
  --bucket raydenrules-data \
  --id EntireBucket \
  --metrics-configuration Id=EntireBucket
```

View metrics in CloudWatch:
- AWS Console → CloudWatch → Metrics → S3

## Best Practices

1. **Versioning:** Enable S3 versioning for production buckets
   ```bash
   aws s3api put-bucket-versioning \
     --bucket raydenrules-data \
     --versioning-configuration Status=Enabled
   ```

2. **Encryption:** Enable server-side encryption
   ```bash
   aws s3api put-bucket-encryption \
     --bucket raydenrules-data \
     --server-side-encryption-configuration \
     '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
   ```

3. **Access Logging:** Enable for audit trail
   ```bash
   aws s3api put-bucket-logging \
     --bucket raydenrules-data \
     --bucket-logging-status file://logging.json
   ```

4. **Backup Strategy:** Use cross-region replication for critical data

## Related Documentation

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Kedro S3 Integration](https://docs.kedro.org/en/stable/data/kedro_io.html)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [S3 Pricing Calculator](https://calculator.aws/#/)
