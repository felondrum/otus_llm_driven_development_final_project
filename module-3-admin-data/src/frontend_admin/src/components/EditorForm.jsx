import React from 'react'

const EditorForm = ({ 
  schema, 
  data = {}, 
  onChange, 
  onSubmit,
  onCancel
}) => {
  const handleChange = (field, value) => {
    if (onChange) {
      onChange({ ...data, [field]: value })
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (onSubmit) {
      onSubmit(data)
    }
  }

  const getFieldType = (field) => {
    if (field.type) return field.type
    
    if (field.enum) return 'select'
    if (field.multiline) return 'textarea'
    if (field.pattern === 'email') return 'email'
    if (field.pattern === 'url') return 'url'
    if (field.typeName === 'number') return 'number'
    
    return 'text'
  }

  return (
    <form className="editor-form" onSubmit={handleSubmit}>
      {schema.map((field) => (
        <div key={field.name} className="form-group">
          <label htmlFor={field.name} className="form-label">
            {field.label}
            {field.required && <span className="required">*</span>}
          </label>
          
          {getFieldType(field) === 'textarea' ? (
            <textarea
              id={field.name}
              name={field.name}
              value={data[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              disabled={field.readOnly}
              className="form-control"
              rows={field.rows || 3}
            />
          ) : field.enum ? (
            <select
              id={field.name}
              name={field.name}
              value={data[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              disabled={field.readOnly}
              className="form-control"
            >
              <option value="">Select {field.label}</option>
              {field.enum.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              id={field.name}
              name={field.name}
              type={getFieldType(field)}
              value={data[field.name] || ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              disabled={field.readOnly}
              className="form-control"
            />
          )}
          
          {field.description && (
            <small className="form-help">{field.description}</small>
          )}
        </div>
      ))}

      <div className="form-actions">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn btn-secondary">
            Cancel
          </button>
        )}
        <button type="submit" className="btn btn-primary">
          {data.id ? 'Update' : 'Create'}
        </button>
      </div>
    </form>
  )
}

export default EditorForm
