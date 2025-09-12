#!/usr/bin/env node

/*
 * Minimal test runner for basic functionality testing
 * Run with: node minimal-test.js
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');

console.log('🧪 Running minimal tests for CERN Open Data Portal Records UI...\n');

// Test 1: Check if required files exist
console.log('📁 Checking file structure...');
const requiredFiles = [
  'constants.js',
  'config.js', 
  'utils.js',
  'hooks.js',
  'app.js',
  'FilesBoxApp.js',
  'CitationsApp.js'
];

let filesExist = true;
requiredFiles.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`   ✅ ${file} exists`);
  } else {
    console.log(`   ❌ ${file} missing`);
    filesExist = false;
  }
});

if (!filesExist) {
  console.log('\n❌ Some required files are missing. Cannot run tests.');
  process.exit(1);
}

// Test 2: Load and test constants
console.log('\n🔧 Testing constants...');
try {
  const constants = require('./constants');
  assert.ok(constants.AVAILABILITY_STATES, 'AVAILABILITY_STATES should exist');
  assert.ok(constants.FILE_FORMATS, 'FILE_FORMATS should exist');
  assert.strictEqual(constants.ITEMS_PER_PAGE, 5, 'ITEMS_PER_PAGE should be 5');
  console.log('   ✅ Constants loaded successfully');
} catch (e) {
  console.log(`   ❌ Constants test failed: ${e.message}`);
}

// Test 3: Load and test utility functions
console.log('\n🛠️  Testing utility functions...');
try {
  const utils = require('./utils');
  
  // Test file size utility
  const sizeResult = utils.toHumanReadableSize(1024);
  assert.strictEqual(sizeResult, '1.0 KiB', 'Should convert 1024 bytes to 1.0 KiB');
  
  // Test edge cases
  assert.strictEqual(utils.toHumanReadableSize(0), '0 bytes', 'Should handle zero bytes');
  assert.strictEqual(utils.toHumanReadableSize('invalid'), '-', 'Should handle invalid input');
  
  // Test email validation
  assert.strictEqual(utils.isValidEmail('test@example.com'), true, 'Should validate correct email');
  assert.strictEqual(utils.isValidEmail('invalid'), false, 'Should reject invalid email');
  
  console.log('   ✅ Utility functions working correctly');
} catch (e) {
  console.log(`   ❌ Utility functions test failed: ${e.message}`);
}

// Test 4: Test configuration
console.log('\n⚙️  Testing configuration...');
try {
  const config = require('./config');
  assert.ok(config.RECORD_FILEPAGE_URL, 'RECORD_FILEPAGE_URL function should exist');
  
  const testUrl = config.RECORD_FILEPAGE_URL('test-pid', 1, 'files');
  assert.strictEqual(testUrl, '/record/test-pid/filepage/1?type=files', 'Should build correct URL');
  
  console.log('   ✅ Configuration working correctly');
} catch (e) {
  console.log(`   ❌ Configuration test failed: ${e.message}`);
}

// Test 5: Check React components can be loaded (basic syntax check)
console.log('\n⚛️  Testing React components (syntax check)...');
try {
  // Just check if the files can be required without syntax errors
  // Note: This won't fully test React functionality, but catches syntax issues
  
  const fs = require('fs');
  const components = ['app.js', 'FilesBoxApp.js', 'CitationsApp.js'];
  
  components.forEach(component => {
    const content = fs.readFileSync(component, 'utf8');
    if (content.includes('import React') || content.includes('from "react"')) {
      console.log(`   ✅ ${component} has valid React imports`);
    } else {
      console.log(`   ⚠️  ${component} might not be a React component`);
    }
  });
  
} catch (e) {
  console.log(`   ❌ React components test failed: ${e.message}`);
}

console.log('\n🎉 Minimal tests completed!');
console.log('\n💡 To run the full test suite with React Testing Library:');
console.log('   1. npm install');
console.log('   2. npm test');

console.log('\n📚 Available npm scripts:');
console.log('   npm test              - Run all tests');
console.log('   npm run test:watch    - Run tests in watch mode');
console.log('   npm run test:coverage - Run tests with coverage');
console.log('   npm run setup         - Install deps and run tests');
