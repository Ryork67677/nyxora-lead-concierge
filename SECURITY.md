# Security policy

## Supported version

Only the latest version on the `main` branch is supported during this portfolio phase.

## Reporting a vulnerability

Please use GitHub private vulnerability reporting instead of opening a public issue. Include the
affected endpoint, reproduction steps, expected impact, and any suggested mitigation. Do not
include real customer, patient, or credential data.

## Known limitations

This repository is an educational portfolio project. It has not completed a healthcare compliance
review, penetration test, clinical review, or production privacy assessment. It should not receive
protected health information or be used to make medical or treatment decisions.

Version 0.3 adds production-required bearer authentication, privacy-safe structured request logs,
dependency auditing, bounded Prometheus metrics, trusted-host validation, hardened container
settings, and explicit failure responses. These controls improve the engineering baseline but do
not constitute healthcare compliance or a completed security review.

Before any real-world deployment, add role authorization and external identity, edge rate limiting,
managed secret storage, TLS, encrypted managed storage, backup and data-retention enforcement,
central audit retention, penetration testing, and independent security, privacy, legal, and clinical
review.

