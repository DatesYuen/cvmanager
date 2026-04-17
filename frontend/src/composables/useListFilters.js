import { ref } from 'vue'

export function useListFilters() {
  const filterStates = ref({})

  function ensureFilterState(tabKey) {
    if (!filterStates.value[tabKey]) {
      filterStates.value[tabKey] = {
        keyword: '',
        filters: [],
      }
    }
    return filterStates.value[tabKey]
  }

  function resetFilterState(tabKey) {
    filterStates.value[tabKey] = {
      keyword: '',
      filters: [],
    }
  }

  function addFilter(tabKey) {
    ensureFilterState(tabKey).filters.push({ field: '', op: 'contains', value: '' })
  }

  function removeFilter(tabKey, index) {
    ensureFilterState(tabKey).filters.splice(index, 1)
  }

  function getFilterableColumns(tab) {
    return (tab.columns || [])
      .filter(col => !!col.prop)
      .map(col => ({ prop: col.prop, label: col.label || col.prop }))
  }

  function getFilteredRows(tab, rows) {
    const state = ensureFilterState(tab.key)
    let result = [...(rows || [])]

    if (state.keyword.trim()) {
      const keyword = state.keyword.trim().toLowerCase()
      result = result.filter(row =>
        getSearchableText(tab, row).toLowerCase().includes(keyword)
      )
    }

    state.filters.forEach(filter => {
      if (!filter.field || filter.value === '' || filter.value === null || filter.value === undefined) return
      const right = normalizeValue(filter.value).toLowerCase()

      if (filter.op === 'contains') {
        result = result.filter(row => normalizeValue(getRowFieldValue(filter.field, row)).toLowerCase().includes(right))
      } else if (filter.op === 'eq') {
        result = result.filter(row => normalizeValue(getRowFieldValue(filter.field, row)).toLowerCase() === right)
      } else if (filter.op === 'ne') {
        result = result.filter(row => normalizeValue(getRowFieldValue(filter.field, row)).toLowerCase() !== right)
      }
    })

    return result
  }

  function getSearchableText(tab, row) {
    return getFilterableColumns(tab)
      .map(col => normalizeValue(getRowFieldValue(col.prop, row)))
      .join(' ')
  }

  function getRowFieldValue(field, row) {
    if (field === 'authors') {
      return (row?.authors || []).map(a => `${a.name}${a.is_corresponding_author ? '*' : ''}`).join(', ')
    }
    if (field === 'applicants') {
      return (row?.applicants || []).map(a => a.name).join(', ')
    }
    if (field === 'attachments') {
      return (row?.attachments || []).map(a => a.original_filename || '').join(', ')
    }
    return row?.[field]
  }

  function normalizeValue(value) {
    if (value === null || value === undefined) return ''
    if (typeof value === 'boolean') return value ? 'true 是' : 'false 否'
    if (Array.isArray(value)) return value.join(', ')
    return String(value)
  }

  return {
    filterStates,
    ensureFilterState,
    resetFilterState,
    addFilter,
    removeFilter,
    getFilterableColumns,
    getFilteredRows,
  }
}
