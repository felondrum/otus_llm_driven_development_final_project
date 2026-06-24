import React from 'react'
import { useState } from 'react'

const DataTable = ({ 
  columns, 
  data, 
  onEdit, 
  onDelete, 
  onRefresh, 
  getRowKey, 
  formatSize, 
  formatBoolean, 
  formatDate 
}) => {
  const [sortConfig, setSortConfig] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [rowsPerPage] = useState(10)

  // Extract rows from data (handle both array and object with data property)
  const extractRows = () => {
    if (!data) return []
    if (Array.isArray(data)) return data
    if (typeof data === 'object') {
      return data.profiles || data.rules || data.styles || data.documents || []
    }
    return []
  }

  const rows = extractRows()

  const defaultGetRowKey = (row, index) => 
    row.row_id || row.document_id || row.rule_id || row.style_id || row.user_id || index
  const rowKeyFn = getRowKey || defaultGetRowKey

  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  const handleSearch = (e) => {
    setSearchQuery(e.target.value)
    setCurrentPage(1)
  }

  // Helper function to render cell value with proper formatting
  const renderCellValue = (value, column, row) => {
    if (column.render) {
      return column.render(row)
    }
    if (value === null || value === undefined) {
      return <span className="unknown-value">N/A</span>
    }
    if (value === '') {
      return <span className="empty-value">-</span>
    }
    
    // Format file size
    if (column.key === 'file_size' && formatSize) {
      return formatSize(value)
    }
    
    // Format boolean values
    if (typeof value === 'boolean' && formatBoolean) {
      return formatBoolean(value)
    }
    
    // Format status
    if (column.key === 'status' && value) {
      const statusClass = value === 'indexed' ? 'status-indexed' : 
                         value === 'processing' ? 'status-processing' : 
                         value === 'failed' ? 'status-failed' : 'status-unknown'
      return <span className={`status-badge ${statusClass}`}>{value}</span>
    }
    
    return String(value)
  }

  const filteredData = rows.filter((row) => {
    return Object.values(row).some((value) =>
      String(value).toLowerCase().includes(searchQuery.toLowerCase())
    )
  })

  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortConfig) return 0
    const { key, direction } = sortConfig
    const aVal = a[key]
    const bVal = b[key]

    if (aVal < bVal) return direction === 'asc' ? -1 : 1
    if (aVal > bVal) return direction === 'asc' ? 1 : -1
    return 0
  })

  const paginatedData = sortedData.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  )

  const totalPages = Math.ceil(filteredData.length / rowsPerPage)

  return (
    <div className="data-table">
      {rows.length > 0 && (
        <>
          <div className="table-controls">
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={handleSearch}
              className="search-input"
            />
            {onRefresh && (
              <button onClick={onRefresh} className="btn btn-primary">
                Refresh
              </button>
            )}
          </div>

          <table className="table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    onClick={() => handleSort(column.key)}
                    className={sortConfig?.key === column.key ? 'sorted' : ''}
                    style={column.width ? { width: column.width } : {}}
                  >
                    {column.label}
                    {sortConfig?.key === column.key &&
                      (sortConfig.direction === 'asc' ? ' ↑' : ' ↓')}
                  </th>
                ))}
                {(onEdit || onDelete) && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {paginatedData.length > 0 ? (
                paginatedData.map((row, index) => (
                  <tr key={rowKeyFn(row, index)}>
                    {columns.map((column) => (
                      <td key={`${column.key}-${rowKeyFn(row, index)}`}>
                        {renderCellValue(row[column.key], column, row)}
                      </td>
                    ))}
                    {(onEdit || onDelete) && (
                      <td className="actions">
                        {onEdit && (
                          <button
                            onClick={() => onEdit(row)}
                            className="btn btn-sm btn-primary"
                          >
                            Edit
                          </button>
                        )}
                        {onDelete && (
                          <button
                            onClick={() => onDelete(row)}
                            className="btn btn-sm btn-danger"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={columns.length + (onEdit || onDelete ? 1 : 0)} className="no-data">
                    No data available
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              <span>
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
      {rows.length === 0 && (
        <div className="no-data" style={{ padding: '40px', textAlign: 'center' }}>
          No data available
        </div>
      )}
    </div>
  )
}

export default DataTable
