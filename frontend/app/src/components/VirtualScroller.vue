<template>
  <div 
    ref="container"
    class="virtual-scroller"
    :style="containerStyle"
    @scroll="handleScroll"
  >
    <!-- Spacer for items before visible range -->
    <div 
      v-if="offsetY > 0"
      :style="{ height: `${offsetY}px` }"
      class="virtual-spacer-top"
    ></div>

    <!-- Visible items -->
    <div
      v-for="item in visibleItems"
      :key="getItemKey(item)"
      :style="getItemStyle(item)"
      class="virtual-item"
    >
      <slot 
        :item="item.data"
        :index="item.index"
        :visible="item.visible"
      ></slot>
    </div>

    <!-- Spacer for items after visible range -->
    <div 
      v-if="bottomSpacerHeight > 0"
      :style="{ height: `${bottomSpacerHeight}px` }"
      class="virtual-spacer-bottom"
    ></div>

    <!-- Loading indicator -->
    <div 
      v-if="loading && hasMore"
      class="virtual-loading flex items-center justify-center py-4"
    >
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
      <span class="ml-2 text-sm text-gray-600 dark:text-gray-400">Loading more...</span>
    </div>

    <!-- End of list indicator -->
    <div 
      v-else-if="!hasMore && items.length > 0"
      class="virtual-end text-center py-4 text-sm text-gray-500 dark:text-gray-400"
    >
      {{ endMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';

const props = defineProps({
  items: {
    type: Array,
    required: true
  },
  itemHeight: {
    type: [Number, Function],
    default: 200
  },
  containerHeight: {
    type: Number,
    default: 600
  },
  overscan: {
    type: Number,
    default: 5
  },
  keyField: {
    type: String,
    default: 'id'
  },
  loading: {
    type: Boolean,
    default: false
  },
  hasMore: {
    type: Boolean,
    default: true
  },
  loadMoreThreshold: {
    type: Number,
    default: 200
  },
  endMessage: {
    type: String,
    default: 'No more items to load'
  },
  estimatedItemHeight: {
    type: Number,
    default: 200
  },
  horizontal: {
    type: Boolean,
    default: false
  },
  gridCols: {
    type: Number,
    default: 1
  }
});

const emit = defineEmits(['scroll', 'load-more', 'item-visible', 'item-hidden']);

// Reactive state
const container = ref(null);
const scrollTop = ref(0);
const scrollLeft = ref(0);
const containerWidth = ref(0);
const containerHeightRef = ref(props.containerHeight);
const itemHeights = ref(new Map());
const itemPositions = ref(new Map());
const measuredItems = ref(new Set());

// Computed properties
const containerStyle = computed(() => ({
  height: `${containerHeightRef.value}px`,
  overflow: 'auto',
  position: 'relative'
}));

const totalHeight = computed(() => {
  if (props.items.length === 0) return 0;
  
  let height = 0;
  for (let i = 0; i < props.items.length; i++) {
    height += getItemHeight(i);
  }
  return height;
});

const visibleRange = computed(() => {
  const start = Math.floor(scrollTop.value / getAverageItemHeight()) - props.overscan;
  const visibleCount = Math.ceil(containerHeightRef.value / getAverageItemHeight()) + props.overscan * 2;
  
  return {
    start: Math.max(0, start),
    end: Math.min(props.items.length - 1, start + visibleCount)
  };
});

const visibleItems = computed(() => {
  const items = [];
  let currentY = 0;
  
  for (let i = 0; i <= visibleRange.value.end; i++) {
    if (i < visibleRange.value.start) {
      currentY += getItemHeight(i);
      continue;
    }
    
    const item = props.items[i];
    if (!item) continue;
    
    items.push({
      data: item,
      index: i,
      y: currentY,
      height: getItemHeight(i),
      visible: true
    });
    
    currentY += getItemHeight(i);
  }
  
  return items;
});

const offsetY = computed(() => {
  let offset = 0;
  for (let i = 0; i < visibleRange.value.start; i++) {
    offset += getItemHeight(i);
  }
  return offset;
});

const bottomSpacerHeight = computed(() => {
  let height = 0;
  for (let i = visibleRange.value.end + 1; i < props.items.length; i++) {
    height += getItemHeight(i);
  }
  return height;
});

// Methods
const getItemHeight = (index) => {
  if (typeof props.itemHeight === 'function') {
    return props.itemHeight(props.items[index], index);
  }
  
  // Use measured height if available
  if (itemHeights.value.has(index)) {
    return itemHeights.value.get(index);
  }
  
  return props.itemHeight || props.estimatedItemHeight;
};

const getAverageItemHeight = () => {
  if (itemHeights.value.size === 0) {
    return props.estimatedItemHeight;
  }
  
  const heights = Array.from(itemHeights.value.values());
  return heights.reduce((sum, height) => sum + height, 0) / heights.length;
};

const getItemKey = (item) => {
  return item.data[props.keyField] || item.index;
};

const getItemStyle = (item) => {
  return {
    position: 'absolute',
    top: `${item.y}px`,
    left: '0',
    right: '0',
    height: `${item.height}px`,
    transform: 'translateZ(0)' // Force GPU acceleration
  };
};

const handleScroll = (event) => {
  const target = event.target;
  scrollTop.value = target.scrollTop;
  scrollLeft.value = target.scrollLeft;
  
  emit('scroll', {
    scrollTop: scrollTop.value,
    scrollLeft: scrollLeft.value,
    scrollHeight: target.scrollHeight,
    clientHeight: target.clientHeight
  });
  
  // Check if we need to load more items
  if (props.hasMore && !props.loading) {
    const distanceToBottom = target.scrollHeight - target.scrollTop - target.clientHeight;
    if (distanceToBottom < props.loadMoreThreshold) {
      emit('load-more');
    }
  }
  
  // Emit visibility events
  checkItemVisibility();
};

const checkItemVisibility = () => {
  const containerRect = container.value?.getBoundingClientRect();
  if (!containerRect) return;
  
  visibleItems.value.forEach(item => {
    const itemTop = item.y - scrollTop.value;
    const itemBottom = itemTop + item.height;
    
    const isVisible = itemBottom > 0 && itemTop < containerHeightRef.value;
    
    if (isVisible && !item.wasVisible) {
      emit('item-visible', item.data, item.index);
      item.wasVisible = true;
    } else if (!isVisible && item.wasVisible) {
      emit('item-hidden', item.data, item.index);
      item.wasVisible = false;
    }
  });
};

const measureItem = (index, height) => {
  if (height && height !== itemHeights.value.get(index)) {
    itemHeights.value.set(index, height);
    measuredItems.value.add(index);
    
    // Trigger re-calculation of positions
    nextTick(() => {
      updateItemPositions();
    });
  }
};

const updateItemPositions = () => {
  let currentY = 0;
  
  for (let i = 0; i < props.items.length; i++) {
    itemPositions.value.set(i, currentY);
    currentY += getItemHeight(i);
  }
};

const scrollToIndex = (index, behavior = 'smooth') => {
  if (!container.value || index < 0 || index >= props.items.length) return;
  
  let targetY = 0;
  for (let i = 0; i < index; i++) {
    targetY += getItemHeight(i);
  }
  
  container.value.scrollTo({
    top: targetY,
    behavior
  });
};

const scrollToTop = (behavior = 'smooth') => {
  if (!container.value) return;
  
  container.value.scrollTo({
    top: 0,
    behavior
  });
};

const scrollToBottom = (behavior = 'smooth') => {
  if (!container.value) return;
  
  container.value.scrollTo({
    top: container.value.scrollHeight,
    behavior
  });
};

const getVisibleRange = () => {
  return visibleRange.value;
};

const refresh = () => {
  itemHeights.value.clear();
  itemPositions.value.clear();
  measuredItems.value.clear();
  updateItemPositions();
};

// Lifecycle
onMounted(() => {
  if (container.value) {
    containerHeightRef.value = container.value.clientHeight || props.containerHeight;
    containerWidth.value = container.value.clientWidth;
  }
  
  updateItemPositions();
  
  // Set up ResizeObserver for container
  if (window.ResizeObserver) {
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerHeightRef.value = entry.contentRect.height;
        containerWidth.value = entry.contentRect.width;
      }
    });
    
    if (container.value) {
      resizeObserver.observe(container.value);
    }
    
    onUnmounted(() => {
      resizeObserver.disconnect();
    });
  }
});

// Watch for items changes
watch(() => props.items, () => {
  updateItemPositions();
}, { deep: true });

// Expose methods
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom,
  getVisibleRange,
  refresh,
  measureItem
});
</script>

<style scoped>
.virtual-scroller {
  position: relative;
  overflow: auto;
  will-change: scroll-position;
}

.virtual-item {
  will-change: transform;
}

.virtual-spacer-top,
.virtual-spacer-bottom {
  pointer-events: none;
}

/* Smooth scrolling */
.virtual-scroller {
  scroll-behavior: smooth;
}

/* Hide scrollbar on webkit browsers */
.virtual-scroller::-webkit-scrollbar {
  width: 8px;
}

.virtual-scroller::-webkit-scrollbar-track {
  background: transparent;
}

.virtual-scroller::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 4px;
}

.virtual-scroller::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7);
}
</style>
