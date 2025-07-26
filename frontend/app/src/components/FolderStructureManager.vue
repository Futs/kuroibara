<template>
  <div class="folder-structure-manager">
    <div class="header">
      <h3>Folder Structure Management</h3>
      <p class="subtitle">
        Manage how your manga files are organized and migrate between different folder structures.
      </p>
    </div>

    <!-- Current Settings -->
    <div class="current-settings card">
      <h4>Current Settings</h4>
      <div class="setting-item">
        <label>Manga Folder Template:</label>
        <code>{{ currentSettings.naming_format_manga }}</code>
      </div>
      <div class="setting-item">
        <label>Chapter File Template:</label>
        <code>{{ currentSettings.naming_format_chapter }}</code>
      </div>
      <div class="setting-item">
        <label>Structure Pattern:</label>
        <span class="pattern-badge" :class="currentSettings.preferred_structure_pattern">
          {{ getPatternLabel(currentSettings.preferred_structure_pattern) }}
        </span>
      </div>
    </div>

    <!-- Template Presets -->
    <div class="template-presets card">
      <h4>Available Templates</h4>
      <div class="presets-grid">
        <div 
          v-for="(template, name) in availableTemplates" 
          :key="name"
          class="preset-card"
          :class="{ active: selectedTemplate === name }"
          @click="selectTemplate(name)"
        >
          <div class="preset-header">
            <h5>{{ formatPresetName(name) }}</h5>
            <span class="preset-type">{{ getPresetType(name) }}</span>
          </div>
          <div class="preset-description">
            {{ templateDescriptions[name] }}
          </div>
          <div class="preset-example">
            <strong>Example:</strong>
            <code>{{ templateExamples[name] }}</code>
          </div>
        </div>
      </div>
    </div>

    <!-- Volume Analysis -->
    <div v-if="selectedManga" class="volume-analysis card">
      <h4>Volume Analysis for "{{ selectedManga.title }}"</h4>
      <div v-if="volumeAnalysis" class="analysis-results">
        <div class="analysis-stats">
          <div class="stat">
            <span class="label">Total Chapters:</span>
            <span class="value">{{ volumeAnalysis.analysis.chapter_count }}</span>
          </div>
          <div class="stat">
            <span class="label">Chapters with Volumes:</span>
            <span class="value">{{ volumeAnalysis.analysis.chapters_with_volumes }}</span>
          </div>
          <div class="stat">
            <span class="label">Unique Volumes:</span>
            <span class="value">{{ volumeAnalysis.analysis.volume_count }}</span>
          </div>
          <div class="stat">
            <span class="label">Confidence:</span>
            <span class="value confidence" :class="getConfidenceClass(volumeAnalysis.analysis.confidence_score)">
              {{ (volumeAnalysis.analysis.confidence_score * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
        
        <div class="recommendation">
          <h5>Recommendation</h5>
          <div class="recommended-pattern">
            <span class="pattern-badge" :class="volumeAnalysis.analysis.recommended_pattern">
              {{ getPatternLabel(volumeAnalysis.analysis.recommended_pattern) }}
            </span>
            <p>{{ getRecommendationText(volumeAnalysis.analysis) }}</p>
          </div>
        </div>

        <div v-if="volumeAnalysis.analysis.unique_volumes.length > 0" class="volume-list">
          <h5>Detected Volumes</h5>
          <div class="volumes">
            <span 
              v-for="volume in volumeAnalysis.analysis.unique_volumes" 
              :key="volume"
              class="volume-tag"
            >
              Volume {{ volume }}
            </span>
          </div>
        </div>
      </div>
      
      <div v-else class="analysis-loading">
        <div class="spinner"></div>
        <span>Analyzing volume structure...</span>
      </div>
    </div>

    <!-- Migration Preview -->
    <div v-if="migrationPlan" class="migration-preview card">
      <h4>Migration Preview</h4>
      <div class="migration-summary">
        <div class="summary-stats">
          <div class="stat">
            <span class="label">Operations:</span>
            <span class="value">{{ migrationPlan.summary.total_operations }}</span>
          </div>
          <div class="stat">
            <span class="label">Estimated Size:</span>
            <span class="value">{{ migrationPlan.summary.estimated_size_mb }} MB</span>
          </div>
          <div class="stat">
            <span class="label">Estimated Time:</span>
            <span class="value">{{ migrationPlan.summary.estimated_time_minutes }} min</span>
          </div>
        </div>

        <div v-if="migrationPlan.summary.warnings.length > 0" class="warnings">
          <h5>Warnings</h5>
          <ul>
            <li v-for="warning in migrationPlan.summary.warnings" :key="warning">
              {{ warning }}
            </li>
          </ul>
        </div>

        <div v-if="migrationPlan.summary.risks.length > 0" class="risks">
          <h5>Risks</h5>
          <ul>
            <li v-for="risk in migrationPlan.summary.risks" :key="risk">
              {{ risk }}
            </li>
          </ul>
        </div>
      </div>

      <div class="sample-operations">
        <h5>Sample Operations</h5>
        <div class="operations-list">
          <div 
            v-for="(operation, index) in migrationPlan.preview.sample_operations" 
            :key="index"
            class="operation-item"
          >
            <div class="operation-type">
              <span class="type-badge" :class="operation.type">{{ operation.type }}</span>
            </div>
            <div class="operation-details">
              <div class="source">From: <code>{{ operation.source }}</code></div>
              <div class="target">To: <code>{{ operation.target }}</code></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="actions">
      <button 
        v-if="selectedManga && !volumeAnalysis"
        @click="analyzeVolumes"
        class="btn btn-secondary"
        :disabled="analyzingVolumes"
      >
        <span v-if="analyzingVolumes">Analyzing...</span>
        <span v-else>Analyze Volume Structure</span>
      </button>

      <button 
        v-if="selectedTemplate && selectedManga"
        @click="createMigrationPlan"
        class="btn btn-secondary"
        :disabled="creatingPlan"
      >
        <span v-if="creatingPlan">Creating Plan...</span>
        <span v-else>Preview Migration</span>
      </button>

      <button 
        v-if="migrationPlan"
        @click="executeMigration"
        class="btn btn-primary"
        :disabled="executingMigration"
      >
        <span v-if="executingMigration">Executing...</span>
        <span v-else>Execute Migration</span>
      </button>

      <button 
        @click="$emit('close')"
        class="btn btn-outline"
      >
        Close
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import { api } from '@/services/api'

// Props
const props = defineProps({
  selectedManga: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['close', 'migration-completed'])

// Composables
const { showToast } = useToast()

// Reactive data
const currentSettings = ref({})
const availableTemplates = ref({})
const templateDescriptions = ref({})
const templateExamples = ref({})
const selectedTemplate = ref('')
const volumeAnalysis = ref(null)
const migrationPlan = ref(null)
const analyzingVolumes = ref(false)
const creatingPlan = ref(false)
const executingMigration = ref(false)

// Computed
const getPatternLabel = (pattern) => {
  const labels = {
    'volume_based': 'Volume-Based',
    'chapter_based': 'Chapter-Based',
    'auto_detect': 'Auto-Detect'
  }
  return labels[pattern] || pattern
}

const formatPresetName = (name) => {
  return name.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const getPresetType = (name) => {
  if (name.includes('volume')) return 'Volume-Based'
  if (name.includes('chapter')) return 'Chapter-Based'
  return 'Other'
}

const getConfidenceClass = (score) => {
  if (score >= 0.8) return 'high'
  if (score >= 0.6) return 'medium'
  return 'low'
}

const getRecommendationText = (analysis) => {
  if (analysis.recommended_pattern === 'volume_based') {
    return 'This manga appears to use volumes. A volume-based structure is recommended.'
  } else {
    return 'This manga appears to be volume-less or has inconsistent volume data. A chapter-based structure is recommended.'
  }
}

// Methods
const loadTemplates = async () => {
  try {
    const response = await api.get('/organizer/templates')
    currentSettings.value = {
      naming_format_manga: response.data.current_manga_template,
      naming_format_chapter: response.data.current_chapter_template,
      preferred_structure_pattern: 'auto_detect' // Default for now
    }
    availableTemplates.value = response.data.available_presets
    templateDescriptions.value = response.data.preset_descriptions
    templateExamples.value = response.data.examples
  } catch (error) {
    console.error('Error loading templates:', error)
    showToast('Failed to load templates', 'error')
  }
}

const selectTemplate = (templateName) => {
  selectedTemplate.value = templateName
  // Clear previous analysis when template changes
  migrationPlan.value = null
}

const analyzeVolumes = async () => {
  if (!props.selectedManga) return
  
  analyzingVolumes.value = true
  try {
    const response = await api.post(`/organizer/migration/analyze-volume-usage/${props.selectedManga.id}`)
    volumeAnalysis.value = response.data
  } catch (error) {
    console.error('Error analyzing volumes:', error)
    showToast('Failed to analyze volume structure', 'error')
  } finally {
    analyzingVolumes.value = false
  }
}

const createMigrationPlan = async () => {
  if (!props.selectedManga || !selectedTemplate.value) return
  
  creatingPlan.value = true
  try {
    const template = availableTemplates.value[selectedTemplate.value]
    const response = await api.post(
      `/organizer/migration/create-plan/${props.selectedManga.id}`,
      null,
      {
        params: {
          new_template: template,
          preserve_original: true
        }
      }
    )
    migrationPlan.value = response.data
  } catch (error) {
    console.error('Error creating migration plan:', error)
    showToast('Failed to create migration plan', 'error')
  } finally {
    creatingPlan.value = false
  }
}

const executeMigration = async () => {
  if (!props.selectedManga || !selectedTemplate.value) return
  
  executingMigration.value = true
  try {
    const template = availableTemplates.value[selectedTemplate.value]
    const response = await api.post(
      `/organizer/migration/execute/${props.selectedManga.id}`,
      null,
      {
        params: {
          new_template: template,
          preserve_original: true
        }
      }
    )
    
    showToast('Migration started successfully', 'success')
    emit('migration-completed', response.data)
    emit('close')
  } catch (error) {
    console.error('Error executing migration:', error)
    showToast('Failed to execute migration', 'error')
  } finally {
    executingMigration.value = false
  }
}

// Watchers
watch(() => props.selectedManga, (newManga) => {
  if (newManga) {
    volumeAnalysis.value = null
    migrationPlan.value = null
  }
})

// Lifecycle
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.folder-structure-manager {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h3 {
  color: var(--text-primary);
  margin-bottom: 8px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.card h4 {
  color: var(--text-primary);
  margin-bottom: 16px;
  font-size: 18px;
}

.card h5 {
  color: var(--text-primary);
  margin-bottom: 12px;
  font-size: 16px;
}

/* Current Settings */
.setting-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.setting-item label {
  font-weight: 500;
  color: var(--text-primary);
  min-width: 150px;
}

.setting-item code {
  background: var(--bg-tertiary);
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.pattern-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.pattern-badge.volume_based {
  background: #e3f2fd;
  color: #1976d2;
}

.pattern-badge.chapter_based {
  background: #f3e5f5;
  color: #7b1fa2;
}

.pattern-badge.auto_detect {
  background: #e8f5e8;
  color: #388e3c;
}

/* Template Presets */
.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.preset-card {
  border: 2px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-card:hover {
  border-color: var(--primary-color);
  background: var(--bg-tertiary);
}

.preset-card.active {
  border-color: var(--primary-color);
  background: var(--primary-color-light);
}

.preset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preset-header h5 {
  margin: 0;
  color: var(--text-primary);
}

.preset-type {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  color: var(--text-secondary);
}

.preset-description {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 12px;
  line-height: 1.4;
}

.preset-example {
  font-size: 12px;
}

.preset-example strong {
  color: var(--text-primary);
}

.preset-example code {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  display: block;
  margin-top: 4px;
  word-break: break-all;
}

/* Volume Analysis */
.analysis-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
}

.stat .label {
  color: var(--text-secondary);
  font-size: 13px;
}

.stat .value {
  color: var(--text-primary);
  font-weight: 600;
}

.confidence.high {
  color: #4caf50;
}

.confidence.medium {
  color: #ff9800;
}

.confidence.low {
  color: #f44336;
}

.recommendation {
  background: var(--bg-tertiary);
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.recommended-pattern {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.recommended-pattern p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.volume-list {
  margin-top: 16px;
}

.volumes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.volume-tag {
  background: var(--primary-color-light);
  color: var(--primary-color);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.analysis-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: var(--text-secondary);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Migration Preview */
.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.warnings, .risks {
  margin-bottom: 16px;
}

.warnings h5 {
  color: #ff9800;
}

.risks h5 {
  color: #f44336;
}

.warnings ul, .risks ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.warnings li, .risks li {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 4px;
}

.operations-list {
  max-height: 300px;
  overflow-y: auto;
}

.operation-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
}

.type-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  white-space: nowrap;
}

.type-badge.move {
  background: #fff3e0;
  color: #f57c00;
}

.type-badge.copy {
  background: #e8f5e8;
  color: #388e3c;
}

.type-badge.create_dir {
  background: #e3f2fd;
  color: #1976d2;
}

.operation-details {
  flex: 1;
  min-width: 0;
}

.operation-details .source,
.operation-details .target {
  font-size: 12px;
  margin-bottom: 4px;
}

.operation-details code {
  background: var(--bg-tertiary);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

/* Actions */
.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  font-size: 14px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-color-dark);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-quaternary);
}

.btn-outline {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-outline:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
</style>
