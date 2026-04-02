/**
 * 邮件模板编辑器组件
 *
 * 功能:
 * - 查看模板列表
 * - 编辑模板内容
 * - 启用/禁用模板
 * - 创建新模板
 */
import React, { useState, useEffect } from 'react';
import { getEmailTemplates, updateTemplate, createTemplate, deleteTemplate } from '../services/emailGenerator';
import type { EmailTemplate } from '../types/generator';

// ============================================================================
// Props Interface
// ============================================================================

export interface TemplateEditorProps {
  onTemplateUpdated?: () => void;
}

// ============================================================================
// TemplateEditor Component
// ============================================================================

const TemplateEditor: React.FC<TemplateEditorProps> = ({ onTemplateUpdated }) => {
  // State
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);

  // 表单状态
  const [formData, setFormData] = useState({
    type: 'rfq',
    product_name: '',
    region: 'Europe',
    quantity_range: '100-500',
    subject_template: '',
    body_template: '',
  });

  // 加载模板列表
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getEmailTemplates();
      setTemplates(response.templates);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 处理编辑
  const handleEdit = (template: EmailTemplate) => {
    setSelectedTemplate(template);
    setFormData({
      type: template.type,
      product_name: template.product_name,
      region: template.region,
      quantity_range: template.quantity_range,
      subject_template: template.subject_template || '',
      body_template: template.body_template || '',
    });
    setShowEditForm(true);
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    if (!selectedTemplate) return;

    setIsLoading(true);
    setError(null);
    try {
      await updateTemplate(selectedTemplate.id, {
        subject_template: formData.subject_template,
        body_template: formData.body_template,
      });
      setShowEditForm(false);
      setSelectedTemplate(null);
      loadTemplates();
      onTemplateUpdated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setShowEditForm(false);
    setSelectedTemplate(null);
  };

  // 切换启用状态
  const handleToggleActive = async (template: EmailTemplate) => {
    setIsLoading(true);
    setError(null);
    try {
      await updateTemplate(template.id, {
        is_active: !template.is_active,
      });
      loadTemplates();
      onTemplateUpdated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 删除模板
  const handleDelete = async (templateId: number) => {
    if (!confirm('确定要删除这个模板吗？')) return;

    setIsLoading(true);
    setError(null);
    try {
      await deleteTemplate(templateId);
      loadTemplates();
      onTemplateUpdated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 创建新模板
  const handleCreate = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await createTemplate(formData);
      setShowCreateForm(false);
      setFormData({
        type: 'rfq',
        product_name: '',
        region: 'Europe',
        quantity_range: '100-500',
        subject_template: '',
        body_template: '',
      });
      loadTemplates();
      onTemplateUpdated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#1e293b] to-[#334155] px-5 py-4 border-b border-[#475569]">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[#e2e8f0]">
            📝 邮件模板管理 | Template Manager
          </h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-[#3b82f6] hover:bg-[#2563eb] text-[#e2e8f0] text-sm font-medium py-2 px-4 rounded-lg transition-all flex items-center gap-2"
          >
            <span className="text-lg">+</span>
            新建模板 | New Template
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        {/* Loading */}
        {isLoading && (
          <div className="text-center text-[#94a3b8] py-8">
            <div className="text-2xl mb-2">⏳</div>
            <div>加载中 | Loading...</div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-[rgba(239,68,68,0.1)] border border-[#ef4444] rounded-lg px-4 py-3 text-sm text-[#ef4444] mb-4">
            {error}
          </div>
        )}

        {/* Create Form */}
        {showCreateForm && !showEditForm && (
          <CreateTemplateForm
            formData={formData}
            setFormData={setFormData}
            onSave={handleCreate}
            onCancel={() => setShowCreateForm(false)}
            isLoading={isLoading}
          />
        )}

        {/* Edit Form */}
        {showEditForm && selectedTemplate && (
          <EditTemplateForm
            formData={formData}
            setFormData={setFormData}
            onSave={handleSaveEdit}
            onCancel={handleCancelEdit}
            isLoading={isLoading}
          />
        )}

        {/* Template List */}
        {!showCreateForm && (
          <div className="space-y-3">
            {templates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onEdit={handleEdit}
                onToggleActive={handleToggleActive}
                onDelete={handleDelete}
              />
            ))}
            {templates.length === 0 && (
              <div className="text-center text-[#94a3b8] py-8">
                <div className="text-4xl mb-2">📭</div>
                <div>暂无模板 | No Templates</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Template Card Component
// ============================================================================

interface TemplateCardProps {
  template: EmailTemplate;
  onEdit: (template: EmailTemplate) => void;
  onToggleActive: (template: EmailTemplate) => void;
  onDelete: (templateId: number) => void;
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  onEdit,
  onToggleActive,
  onDelete,
}) => {
  const getTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      rfq: 'bg-[rgba(59,130,246,0.2)] text-[#3b82f6]',
      inquiry: 'bg-[rgba(16,185,129,0.2)] text-[#10b981]',
      complaint: 'bg-[rgba(239,68,68,0.2)] text-[#ef4444]',
      status_check: 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b]',
    };
    return colors[type] || 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]';
  };

  return (
    <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4 hover:border-[#3b82f6] transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-1 rounded font-medium ${getTypeBadge(template.type)}`}>
            {template.type.toUpperCase()}
          </span>
          <span className="text-sm text-[#e2e8f0] font-medium">{template.product_name}</span>
          <span className="text-xs text-[#64748b]">{template.region}</span>
          <span className="text-xs text-[#64748b]">{template.quantity_range}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-1 rounded ${
            template.is_active ? 'bg-[rgba(16,185,129,0.2)] text-[#10b981]' : 'bg-[rgba(100,116,139,0.2)] text-[#94a3b8]'
          }`}>
            {template.is_active ? '已启用' : '已禁用'}
          </span>
          <button
            onClick={() => onEdit(template)}
            className="text-xs bg-[#3b82f6] hover:bg-[#2563eb] text-[#e2e8f0] px-3 py-1 rounded transition-all"
          >
            编辑
          </button>
          <button
            onClick={() => onToggleActive(template)}
            className={`text-xs px-3 py-1 rounded transition-all ${
              template.is_active
                ? 'bg-[rgba(245,158,11,0.2)] text-[#f59e0b] hover:bg-[rgba(245,158,11,0.3)]'
                : 'bg-[rgba(16,185,129,0.2)] text-[#10b981] hover:bg-[rgba(16,185,129,0.3)]'
            }`}
          >
            {template.is_active ? '禁用' : '启用'}
          </button>
          <button
            onClick={() => onDelete(template.id)}
            className="text-xs bg-[rgba(239,68,68,0.2)] text-[#ef4444] hover:bg-[rgba(239,68,68,0.3)] px-3 py-1 rounded transition-all"
          >
            删除
          </button>
        </div>
      </div>
      <div className="text-xs text-[#64748b]">
        <div className="text-[#94a3b8] mb-1">主题模板:</div>
        <div className="font-mono text-[#e2e8f0] truncate">{template.type} - {template.quantity_range}</div>
      </div>
    </div>
  );
};

// ============================================================================
// Create Template Form Component
// ============================================================================

interface CreateTemplateFormProps {
  formData: any;
  setFormData: (data: any) => void;
  onSave: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

const CreateTemplateForm: React.FC<CreateTemplateFormProps> = ({
  formData,
  setFormData,
  onSave,
  onCancel,
  isLoading,
}) => {
  return (
    <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4 mb-4">
      <h3 className="text-lg font-semibold text-[#e2e8f0] mb-4">创建新模板 | Create Template</h3>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">类型 | Type</label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6]"
          >
            <option value="rfq">RFQ</option>
            <option value="inquiry">Inquiry</option>
            <option value="complaint">Complaint</option>
            <option value="status_check">Status Check</option>
          </select>
        </div>

        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">产品 | Product</label>
          <input
            type="text"
            value={formData.product_name}
            onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6]"
            placeholder="e.g. Paracetamol 500mg"
          />
        </div>

        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">地区 | Region</label>
          <select
            value={formData.region}
            onChange={(e) => setFormData({ ...formData, region: e.target.value })}
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6]"
          >
            <option value="Europe">Europe</option>
            <option value="Asia">Asia</option>
            <option value="South America">South America</option>
            <option value="Middle East">Middle East</option>
          </select>
        </div>

        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">数量范围 | Quantity Range</label>
          <input
            type="text"
            value={formData.quantity_range}
            onChange={(e) => setFormData({ ...formData, quantity_range: e.target.value })}
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6]"
            placeholder="e.g. 100-500"
          />
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-xs text-[#94a3b8] mb-1">主题模板 | Subject Template</label>
        <input
          type="text"
          value={formData.subject_template}
          onChange={(e) => setFormData({ ...formData, subject_template: e.target.value })}
          className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6]"
          placeholder="e.g. RFQ: {product} - Quantity {quantity}"
        />
      </div>

      <div className="mb-4">
        <label className="block text-xs text-[#94a3b8] mb-1">正文模板 | Body Template</label>
        <textarea
          value={formData.body_template}
          onChange={(e) => setFormData({ ...formData, body_template: e.target.value })}
          rows={6}
          className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6] font-mono"
          placeholder="Dear Customer,{'\n'}We are interested in {product}..."
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={onSave}
          disabled={isLoading}
          className="bg-[#10b981] hover:bg-[#059669] disabled:bg-[#475569] text-[#e2e8f0] font-medium py-2 px-4 rounded-lg transition-all"
        >
          {isLoading ? '保存中...' : '保存 | Save'}
        </button>
        <button
          onClick={onCancel}
          disabled={isLoading}
          className="bg-[#64748b] hover:bg-[#475569] disabled:bg-[#334155] text-[#e2e8f0] font-medium py-2 px-4 rounded-lg transition-all"
        >
          取消 | Cancel
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// Edit Template Form Component
// ============================================================================

interface EditTemplateFormProps {
  formData: any;
  setFormData: (data: any) => void;
  onSave: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

const EditTemplateForm: React.FC<EditTemplateFormProps> = ({
  formData,
  setFormData,
  onSave,
  onCancel,
  isLoading,
}) => {
  return (
    <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4 mb-4">
      <h3 className="text-lg font-semibold text-[#e2e8f0] mb-4">编辑模板 | Edit Template</h3>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">类型 | Type</label>
          <input
            type="text"
            value={formData.type.toUpperCase()}
            disabled
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#64748b] focus:outline-none cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">产品 | Product</label>
          <input
            type="text"
            value={formData.product_name}
            disabled
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#64748b] focus:outline-none cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">地区 | Region</label>
          <input
            type="text"
            value={formData.region}
            disabled
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#64748b] focus:outline-none cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-xs text-[#94a3b8] mb-1">数量范围 | Quantity Range</label>
          <input
            type="text"
            value={formData.quantity_range}
            disabled
            className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#64748b] focus:outline-none cursor-not-allowed"
          />
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-xs text-[#94a3b8] mb-1">主题模板 | Subject Template</label>
        <input
          type="text"
          value={formData.subject_template}
          onChange={(e) => setFormData({ ...formData, subject_template: e.target.value })}
          className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6]"
          placeholder="e.g. RFQ: {product} - Quantity {quantity}"
        />
      </div>

      <div className="mb-4">
        <label className="block text-xs text-[#94a3b8] mb-1">正文模板 | Body Template</label>
        <textarea
          value={formData.body_template}
          onChange={(e) => setFormData({ ...formData, body_template: e.target.value })}
          rows={6}
          className="w-full bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] focus:outline-none focus:border-[#3b82f6] font-mono"
          placeholder="Dear Customer,{'\n'}We are interested in {product}..."
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={onSave}
          disabled={isLoading}
          className="bg-[#10b981] hover:bg-[#059669] disabled:bg-[#475569] text-[#e2e8f0] font-medium py-2 px-4 rounded-lg transition-all"
        >
          {isLoading ? '保存中...' : '保存 | Save'}
        </button>
        <button
          onClick={onCancel}
          disabled={isLoading}
          className="bg-[#64748b] hover:bg-[#475569] disabled:bg-[#334155] text-[#e2e8f0] font-medium py-2 px-4 rounded-lg transition-all"
        >
          取消 | Cancel
        </button>
      </div>
    </div>
  );
};

export default TemplateEditor;
