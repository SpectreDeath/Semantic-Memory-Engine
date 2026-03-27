---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Reference
name: tpm-echo-reference
Source: Semantic Memory Engine (SME)
Source_File: extensions/ext_sample_echo/
---

## Purpose

Reference implementation of TPM (Trusted Platform Module) signing and echo verification for extension development.

## Description

The Sample Echo provides a reference implementation for TPM-signed verification. It demonstrates the standard pattern for creating TPM-signed tool outputs and is used as a boilerplate for developing new extensions with proper signing requirements.

## Workflow

1. **TPM Initialization**: Initialize TPM context
2. **Key Management**: Handle TPM key operations
3. **Signing**: Create TPM-signed payloads
4. **Verification**: Verify TPM signatures
5. **Echo Response**: Return signed response

## Examples

### Example 1: TPM-Signed Output
**Input**: Data to sign
**Output**: TPM-signed payload
**Use Case**: Secure output generation

### Example 2: Signature Verification
**Input**: Signed payload
**Output**: Verification result
**Use Case**: Input validation

### Example 3: Extension Template
**Input**: New extension requirements
**Output**: Reference implementation
**Use Case**: Extension development

## Implementation Notes

- **Status**: Reference (✅)
- **Purpose**: Extension boilerplate
- **Extension**: Sample Echo
- **Location**: `D:/SME/extensions/ext_sample_echo/`

## See Also

- [Extension Contract](D:/SME/docs/EXTENSION_CONTRACT.md)
- [Developing Extensions](D:/SME/docs/EXTENSIONS_CATALOG.md)

---
