# MapMyStandards Data Privacy & Confidentiality Response

## For Accreditation Directors

### Does MapMyStandards Violate Privacy/Confidentiality?

**Short Answer: No.** MapMyStandards is designed with educational data privacy and confidentiality in mind. Here's what we do to protect sensitive institutional data:

### 1. Data Processing & Storage

**What data we process:**
- **Document Analysis**: We analyze uploaded documents (policies, procedures, etc.) to map them against accreditation standards
- **Metadata**: We store filename, upload date, and analysis results
- **User Information**: Basic account info (name, email, institution)

**What we DON'T do:**
- We don't share your documents with other institutions
- We don't use your data to train general AI models
- We don't sell or share your data with third parties

### 2. Privacy & Security Features

#### PII Redaction (Built-in)
```python
# From the code: Automatic PII redaction is enabled by default
- Email addresses → [REDACTED_EMAIL]
- Social Security Numbers → [REDACTED_SSN]
- Phone numbers → [REDACTED_PHONE]
- Dates of Birth → [REDACTED_DOB]
```

#### Data Isolation
- Each institution's data is isolated by user account
- Documents are associated with specific user IDs
- No cross-institution data sharing

#### Security Measures
- Encrypted data transmission (HTTPS/TLS)
- Secure authentication (JWT tokens)
- Database-level access controls
- Regular security audits

### 3. Compliance Features

**FERPA Compliance**
- Built-in PII redaction for student information
- Audit trail capabilities
- User access controls

**GDPR/Privacy Rights**
- Data export capabilities
- Right to deletion
- Transparency in data usage

### 4. How Documents Are Processed

1. **Upload**: Document uploaded via secure HTTPS
2. **Redaction**: Optional automatic PII redaction (enabled by default)
3. **Analysis**: AI analyzes content to map to standards
4. **Storage**: Only stores analysis results and redacted content
5. **Access**: Only accessible by the uploading user/institution

### 5. Recommended Usage for Sensitive Data

For maximum privacy protection:

1. **Enable PII Redaction** (on by default)
2. **Remove sensitive information** before upload:
   - Student names and IDs
   - Faculty personal information
   - Financial account numbers
   - Medical/health information

3. **Use institutional policies** rather than individual records
4. **Upload procedural documents** not personal files

### 6. Data Retention & Deletion

- **Active Accounts**: Data retained while account is active
- **Trial Accounts**: Data deleted 30 days after trial expires
- **On Request**: Data can be deleted immediately upon request
- **Exports**: Users can export their data at any time

### 7. Third-Party Services

We use industry-standard, privacy-compliant services:
- **OpenAI API**: For document analysis (enterprise agreement)
- **Stripe**: For payment processing (PCI compliant)
- **Railway/AWS**: For secure cloud hosting

### 8. Transparency Commitment

- Clear privacy policy at `/privacy`
- Audit trails for all document operations
- No hidden data usage
- Regular security updates

### 9. Best Practices for Institutions

1. **Review documents** before upload
2. **Use redacted versions** of sensitive policies
3. **Focus on procedures** not individual cases
4. **Leverage built-in redaction** features
5. **Export data regularly** for your records

### 10. Contact for Privacy Questions

- **Email**: privacy@mapmystandards.ai
- **Review**: Full privacy policy at https://mapmystandards.ai/privacy

### Summary for Accreditation Directors

MapMyStandards is designed to:
- ✅ Protect institutional confidentiality
- ✅ Comply with educational privacy laws (FERPA)
- ✅ Automatically redact PII
- ✅ Isolate each institution's data
- ✅ Provide transparency and control
- ✅ Allow data export and deletion

**Recommendation**: Use MapMyStandards with institutional policies and procedures (not individual student/faculty records) for maximum privacy protection while benefiting from AI-powered accreditation analysis.