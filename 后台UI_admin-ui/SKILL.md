---
name: admin-ui
command: admin-ui
user_invocable: true
description: Admin 后台管理 UI 开发助手。自动激活场景：开发后台管理页面、使用 Ant Design 组件、设计表格/表单/布局时。提供组件规范、交互模式、最佳实践。
---

# Admin 后台管理 UI 开发助手

> 开发后台管理系统时自动融入 Ant Design 最佳实践和 UI 规范

---

## 触发条件

当用户使用以下任一方式时，立即激活此 skill：
- 说"**后台 UI**"或"**Admin 开发**"（主触发词）
- 使用命令：`/admin-ui`
- 说"开发后台页面"、"做一个管理页面"
- 说"Ant Design 怎么用"、"表格怎么写"
- 说"表单怎么做"、"弹窗怎么写"
- 说"数据展示"、"筛选功能"

**适用场景**：
- 开发 Admin/后台管理页面
- 使用 Ant Design 组件
- 设计表格、表单、弹窗、布局
- 讨论数据展示、筛选、操作

---

## 一、页面布局规范

### 1.1 标准页面结构

```tsx
import { PageContainer } from '@/components';

const ListPage: React.FC = () => {
  return (
    <PageContainer
      header={{ title: '页面标题', breadcrumb: { items: [...] } }}
    >
      {/* 筛选区 */}
      <Card style={{ marginBottom: 16 }}>
        <Form layout="inline">...</Form>
      </Card>

      {/* 操作栏 */}
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />}>新增</Button>
      </Space>

      {/* 数据表格 */}
      <Table columns={columns} dataSource={data} />
    </PageContainer>
  );
};
```

### 1.2 间距规范

| 场景 | 间距 | 说明 |
|------|------|------|
| 卡片之间 | 16px | `marginBottom: 16` |
| 表单项之间 | 24px | Form 默认 |
| 按钮组之间 | 8px | Space 默认 |
| 表格与操作栏 | 16px | `marginBottom: 16` |

---

## 二、表格规范 (Table)

### 2.1 列定义模板

```tsx
const columns: ColumnsType<DataType> = [
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name',
    width: 200,           // 固定宽度防止内容撑开
    ellipsis: true,       // 超长截断
    fixed: 'left',        // 重要列固定
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    render: (status) => <StatusTag status={status} />,  // 统一状态展示
  },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    key: 'createTime',
    width: 180,
    sorter: true,         // 支持排序
    render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm'),
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
    fixed: 'right',       // 操作列固定右侧
    render: (_, record) => (
      <Space size="middle">
        <a onClick={() => handleEdit(record)}>编辑</a>
        <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
          <a style={{ color: '#ff4d4f' }}>删除</a>
        </Popconfirm>
      </Space>
    ),
  },
];
```

### 2.2 表格必备配置

```tsx
<Table
  columns={columns}
  dataSource={data}
  rowKey="id"                    // 必须指定唯一 key
  loading={loading}              // 加载状态
  scroll={{ x: 1200 }}           // 横向滚动宽度
  pagination={{
    current: page,
    pageSize: pageSize,
    total: total,
    showSizeChanger: true,       // 允许切换每页条数
    showQuickJumper: true,       // 快速跳转
    showTotal: (total) => `共 ${total} 条`,
  }}
  onChange={handleTableChange}   // 统一处理分页、排序、筛选
/>
```

### 2.3 表格交互规范

| 操作 | 规范 |
|------|------|
| 查看详情 | 点击行或查看按钮 → 抽屉/弹窗 |
| 编辑 | 文字链接"编辑" → 弹窗表单 |
| 删除 | 红色文字 + Popconfirm 二次确认 |
| 批量操作 | 勾选 + 批量按钮在表格上方 |
| 状态切换 | Switch 组件 + 二次确认 |

---

## 三、表单规范 (Form)

### 3.1 表单布局

```tsx
// 弹窗表单：垂直布局
<Form layout="vertical" form={form}>
  <Form.Item label="名称" name="name" rules={[{ required: true }]}>
    <Input placeholder="请输入名称" maxLength={50} showCount />
  </Form.Item>
</Form>

// 筛选表单：行内布局
<Form layout="inline" form={filterForm}>
  <Form.Item label="关键词" name="keyword">
    <Input.Search placeholder="搜索" onSearch={handleSearch} />
  </Form.Item>
  <Form.Item>
    <Space>
      <Button type="primary" onClick={handleSearch}>查询</Button>
      <Button onClick={handleReset}>重置</Button>
    </Space>
  </Form.Item>
</Form>
```

### 3.2 表单校验规范

```tsx
const rules = {
  required: { required: true, message: '此项为必填' },
  phone: { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
  email: { type: 'email', message: '请输入正确的邮箱' },
  maxLength: (max: number) => ({ max, message: `最多输入 ${max} 个字符` }),
};

// 使用
<Form.Item
  label="手机号"
  name="phone"
  rules={[rules.required, rules.phone]}
>
  <Input />
</Form.Item>
```

### 3.3 表单提交流程

```tsx
const handleSubmit = async () => {
  try {
    const values = await form.validateFields();  // 1. 校验
    setSubmitting(true);                          // 2. 显示 loading
    await api.save(values);                       // 3. 提交
    message.success('保存成功');                  // 4. 成功提示
    onSuccess?.();                                // 5. 回调刷新
    handleClose();                                // 6. 关闭弹窗
  } catch (error) {
    // 校验失败不处理，API 错误由全局拦截器处理
    if (error instanceof Error) {
      message.error(error.message);
    }
  } finally {
    setSubmitting(false);                         // 7. 关闭 loading
  }
};
```

---

## 四、弹窗规范 (Modal/Drawer)

### 4.1 Modal vs Drawer 选择

| 场景 | 组件 | 说明 |
|------|------|------|
| 简单表单（≤5 个字段） | Modal | 居中弹窗，聚焦 |
| 复杂表单（>5 个字段） | Drawer | 侧边抽屉，空间大 |
| 查看详情 | Drawer | 不打断当前页面 |
| 确认操作 | Modal.confirm | 系统级确认 |
| 删除确认 | Popconfirm | 轻量级确认 |

### 4.2 Modal 标准写法

```tsx
<Modal
  title={isEdit ? '编辑' : '新增'}
  open={visible}
  onCancel={handleClose}
  onOk={handleSubmit}
  confirmLoading={submitting}
  destroyOnClose              // 关闭时销毁，重置表单
  maskClosable={false}        // 防止误关闭
  width={600}                 // 统一宽度
>
  <Form form={form} layout="vertical">
    ...
  </Form>
</Modal>
```

### 4.3 Drawer 标准写法

```tsx
<Drawer
  title="详情"
  open={visible}
  onClose={handleClose}
  width={600}
  extra={
    <Space>
      <Button onClick={handleClose}>取消</Button>
      <Button type="primary" onClick={handleSubmit} loading={submitting}>
        保存
      </Button>
    </Space>
  }
>
  <Descriptions column={1}>
    <Descriptions.Item label="名称">{data?.name}</Descriptions.Item>
    ...
  </Descriptions>
</Drawer>
```

---

## 五、状态与反馈

### 5.1 加载状态

```tsx
// 页面级加载
<Spin spinning={loading}>
  <Content />
</Spin>

// 按钮加载
<Button type="primary" loading={submitting}>保存</Button>

// 骨架屏（首次加载）
{loading ? <Skeleton active /> : <Content />}
```

### 5.2 空状态

```tsx
<Table
  locale={{
    emptyText: (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="暂无数据"
      >
        <Button type="primary" onClick={handleAdd}>立即创建</Button>
      </Empty>
    ),
  }}
/>
```

### 5.3 操作反馈

| 操作 | 反馈方式 |
|------|---------|
| 保存成功 | `message.success('保存成功')` |
| 删除成功 | `message.success('删除成功')` |
| 操作失败 | `message.error(error.message)` |
| 表单校验失败 | 字段下方红色提示（Form 自动处理） |
| 网络错误 | 全局拦截器统一处理 |

---

## 六、权限控制 UI

### 6.1 按钮级权限

```tsx
import { usePermission } from '@/hooks';

const ListPage: React.FC = () => {
  const { hasPermission } = usePermission();

  return (
    <>
      {hasPermission('user:create') && (
        <Button type="primary">新增</Button>
      )}

      {hasPermission('user:delete') && (
        <Button danger>删除</Button>
      )}
    </>
  );
};
```

### 6.2 菜单权限

```tsx
// 路由配置中标记权限
{
  path: '/users',
  element: <UsersPage />,
  meta: { permission: 'user:list' }
}

// AuthGuard 中过滤无权限路由
```

---

## 七、常用组件模式

### 7.1 搜索选择器 (远程搜索)

```tsx
<Select
  showSearch
  placeholder="搜索用户"
  filterOption={false}
  onSearch={handleSearch}
  loading={searching}
  options={options}
  style={{ width: 200 }}
/>
```

### 7.2 日期范围筛选

```tsx
<Form.Item label="时间范围" name="dateRange">
  <DatePicker.RangePicker
    presets={[
      { label: '今天', value: [dayjs(), dayjs()] },
      { label: '本周', value: [dayjs().startOf('week'), dayjs()] },
      { label: '本月', value: [dayjs().startOf('month'), dayjs()] },
    ]}
  />
</Form.Item>
```

### 7.3 状态筛选

```tsx
<Form.Item label="状态" name="status">
  <Select
    placeholder="全部状态"
    allowClear
    options={[
      { label: '启用', value: 1 },
      { label: '禁用', value: 0 },
    ]}
  />
</Form.Item>
```

---

## 八、代码组织规范

### 8.1 页面文件结构

```
pages/Users/
├── index.tsx           # 列表页主组件
├── components/
│   ├── UserForm.tsx    # 新增/编辑表单
│   ├── UserDetail.tsx  # 详情抽屉
│   └── FilterForm.tsx  # 筛选表单
├── hooks/
│   └── useUserList.ts  # 列表数据 hook
└── types.ts            # 类型定义
```

### 8.2 自定义 Hook 模式

```tsx
// hooks/useUserList.ts
export function useUserList() {
  const [data, setData] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  const fetchData = useCallback(async (params?: QueryParams) => {
    setLoading(true);
    try {
      const res = await api.getUsers(params);
      setData(res.records);
      setPagination(prev => ({ ...prev, total: res.total }));
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, pagination, fetchData };
}
```

---

## 九、检查清单

开发 Admin 页面前确认：

### 布局
- [ ] 使用 PageContainer 包裹？
- [ ] 间距符合规范（16px）？

### 表格
- [ ] 指定 rowKey？
- [ ] 列宽度固定？
- [ ] 分页配置完整？
- [ ] 操作列固定右侧？

### 表单
- [ ] 必填项标记？
- [ ] 校验规则完整？
- [ ] 提交有 loading？
- [ ] 成功有反馈？

### 交互
- [ ] 删除有二次确认？
- [ ] 空状态有处理？
- [ ] 加载状态有显示？
