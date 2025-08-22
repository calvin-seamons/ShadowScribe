# Knowledge Base API Service

This module provides a comprehensive TypeScript API service layer for managing D&D character knowledge base files. It includes full CRUD operations, validation, templates, schemas, and batch operations for character creation workflows.

## Features

- **Complete CRUD Operations**: Create, read, update, and delete knowledge base files
- **Type Safety**: Full TypeScript support with comprehensive type definitions
- **Error Handling**: Robust error handling with custom error types and utilities
- **Validation**: Real-time file content validation against JSON schemas
- **Templates & Schemas**: Access to file templates and JSON schemas for all file types
- **Batch Operations**: Support for batch file operations during character creation
- **Backup Management**: List and restore file backups
- **Character Management**: List existing characters

## Usage

### Basic File Operations

```typescript
import {
  listKnowledgeBaseFiles,
  getFileContent,
  updateFileContent,
  createFile,
  deleteFile
} from './services/knowledgeBaseApi';

// List all knowledge base files
const files = await listKnowledgeBaseFiles();

// Get specific file content
const content = await getFileContent('characters/aragorn/character.json');

// Update file content
await updateFileContent('characters/aragorn/character.json', {
  name: 'Aragorn',
  level: 5
});

// Create new file
await createFile('characters/legolas/character.json', {
  name: 'Legolas',
  race: 'Elf'
});

// Delete file (creates backup)
await deleteFile('characters/old-character/character.json');
```

### Character Management

```typescript
import { listCharacters } from './services/knowledgeBaseApi';

// List all available characters
const { characters, count } = await listCharacters();
```

### Validation

```typescript
import { validateFileContent, getFileSchema } from './services/knowledgeBaseApi';

// Validate file content against schema
const validation = await validateFileContent('character.json', {
  name: 'Test Character',
  level: 1
});

if (!validation.is_valid) {
  console.log('Validation errors:', validation.errors);
}

// Get JSON schema for a file type
const schema = await getFileSchema('character');
```

### Templates

```typescript
import { getFileTemplate, getSupportedFileTypes } from './services/knowledgeBaseApi';

// Get template for creating new files
const template = await getFileTemplate('character');

// Get all supported file types
const supportedTypes = await getSupportedFileTypes();
```

### Batch Operations

```typescript
import { executeBatchFileOperations } from './services/knowledgeBaseApi';

// Execute multiple file operations at once
await executeBatchFileOperations([
  {
    filename: 'characters/party/fighter.json',
    content: { name: 'Fighter', class: 'Fighter' },
    operation: 'create'
  },
  {
    filename: 'characters/party/wizard.json',
    content: { name: 'Wizard', class: 'Wizard' },
    operation: 'create'
  }
]);
```

### Backup Management

```typescript
import { listBackups, restoreBackup } from './services/knowledgeBaseApi';

// List all backups
const backups = await listBackups();

// List backups for specific file
const fileBackups = await listBackups('characters/aragorn/character.json');

// Restore from backup
await restoreBackup('backup-id-123');
```

### Error Handling

```typescript
import {
  getFileContent,
  KnowledgeBaseApiError,
  isKnowledgeBaseApiError,
  getErrorMessage
} from './services/knowledgeBaseApi';

try {
  const content = await getFileContent('nonexistent.json');
} catch (error) {
  if (isKnowledgeBaseApiError(error)) {
    console.log('API Error:', error.message);
    console.log('Status Code:', error.status);
    console.log('Details:', error.details);
  } else {
    console.log('Unknown Error:', getErrorMessage(error));
  }
}
```

## File Types

The service supports the following D&D character file types:

- **character**: Basic character information (character.json)
- **character_background**: Character background and story (character_background.json)
- **feats_and_traits**: Character abilities and features (feats_and_traits.json)
- **action_list**: Character actions and abilities (action_list.json)
- **inventory_list**: Equipment and items (inventory_list.json)
- **objectives_and_contracts**: Quests and contracts (objectives_and_contracts.json)
- **spell_list**: Spell management (spell_list.json)

## Type Definitions

### Core Types

```typescript
interface KnowledgeBaseFile {
  filename: string;
  file_type: 'character' | 'character_background' | 'feats_and_traits' | 'action_list' | 'inventory_list' | 'objectives_and_contracts' | 'spell_list' | 'other';
  size: number;
  last_modified: string;
  is_editable: boolean;
}

interface FileContent {
  filename: string;
  content: Record<string, any>;
  schema_version?: string;
}

interface ValidationError {
  field_path: string;
  message: string;
  error_type: 'required' | 'type' | 'format' | 'custom';
}

interface ValidationResult {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: string[];
}
```



## Error Types

### KnowledgeBaseApiError

Custom error class for API-related errors:

```typescript
class KnowledgeBaseApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  )
}
```

## Utilities

### File Type Detection

```typescript
import { getFileTypeFromFilename, FILE_TYPES } from './services/knowledgeBaseApi';

const fileType = getFileTypeFromFilename('character.json'); // Returns 'character'
```

### Error Utilities

```typescript
import { isKnowledgeBaseApiError, getErrorMessage } from './services/knowledgeBaseApi';

// Check if error is a KnowledgeBaseApiError
const isApiError = isKnowledgeBaseApiError(error);

// Get error message from any error type
const message = getErrorMessage(error);
```

## Testing

The service includes comprehensive tests covering all functionality:

```bash
# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests once
npm run test:run
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **5.5**: Backend provides secure API endpoints for knowledge base operations
- **7.4**: Real-time validation and error handling with clear messaging


## Integration

The service integrates seamlessly with the existing ShadowScribe architecture:

- Uses the same API base URL pattern as existing services
- Follows the same error handling patterns
- Maintains consistency with existing TypeScript types
- Supports the existing WebSocket architecture for real-time updates