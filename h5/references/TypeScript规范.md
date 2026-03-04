# H5 TypeScript 规范

> UniApp + Vue3 + TypeScript 类型定义规范

---

## 一、项目配置

### 1.1 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "esnext",
    "strict": true,
    "jsx": "preserve",
    "moduleResolution": "node",
    "esModuleInterop": true,
    "sourceMap": true,
    "skipLibCheck": true,
    "lib": ["esnext", "dom"],
    "types": ["@dcloudio/types"],
    "paths": {
      "@/*": ["./src/*"]
    },
    "baseUrl": "."
  },
  "include": ["src/**/*.ts", "src/**/*.vue"],
  "exclude": ["node_modules"]
}
```

### 1.2 类型声明文件

```typescript
// shims-uni.d.ts
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 扩展 uni 全局类型
declare namespace UniApp {
  interface Uni {
    $emit: (eventName: string, ...args: any[]) => void
    $on: (eventName: string, callback: (...args: any[]) => void) => void
    $off: (eventName: string, callback?: (...args: any[]) => void) => void
  }
}
```

---

## 二、类型定义位置

### 2.1 目录结构

```
types/
├── api.d.ts           # API 响应类型
├── model.d.ts         # 业务模型类型
├── store.d.ts         # Store 状态类型
└── components.d.ts    # 组件 Props 类型
```

### 2.2 类型定义原则

| 类型 | 位置 | 说明 |
|------|------|------|
| API 响应 | `types/api.d.ts` | 接口返回数据结构 |
| 业务模型 | `types/model.d.ts` | 租客、合同等实体 |
| 组件 Props | 组件文件内 | 与组件放一起 |
| 工具函数参数 | 工具文件内 | 与函数放一起 |

---

## 三、API 类型定义

### 3.1 通用响应类型

```typescript
// types/api.d.ts

// 基础响应
interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页响应
interface PageResult<T> {
  records: T[]
  total: number
  page: number
  size: number
}

// 分页请求参数
interface PageParams {
  pageNo: number
  pageSize: number
}
```

### 3.2 业务 API 类型

```typescript
// types/api.d.ts

// 租客列表请求
interface TenantListParams extends PageParams {
  status?: string
  keyword?: string
}

// 租客列表响应
type TenantListResponse = ApiResponse<PageResult<Tenant>>

// 租客详情响应
type TenantDetailResponse = ApiResponse<Tenant>
```

---

## 四、业务模型类型

### 4.1 实体类型

```typescript
// types/model.d.ts

// 租客
interface Tenant {
  id: number
  name: string
  phone: string
  idCard: string
  status: TenantStatus
  createTime: string
  updateTime: string
}

// 租客状态枚举
type TenantStatus = 'normal' | 'expired' | 'pending'

// 合同
interface Contract {
  id: number
  tenantId: number
  roomId: number
  startDate: string
  endDate: string
  rent: number
  deposit: number
  status: ContractStatus
}

type ContractStatus = 'draft' | 'signed' | 'terminated'
```

### 4.2 表单类型

```typescript
// types/model.d.ts

// 租客表单
interface TenantForm {
  name: string
  phone: string
  idCard: string
  emergencyContact?: string
  emergencyPhone?: string
}

// 表单校验规则
interface FormRule {
  required?: boolean
  message?: string
  pattern?: RegExp
  validator?: (value: any) => boolean | string
}
```

---

## 五、组件类型定义

### 5.1 Props 类型

```vue
<script setup lang="ts">
// 定义 Props 接口
interface Props {
  // 必填
  title: string
  // 可选（带默认值）
  visible?: boolean
  // 数组类型
  options?: OptionItem[]
  // 回调函数
  onConfirm?: (value: string) => void
}

interface OptionItem {
  label: string
  value: string | number
}

// 使用 withDefaults 设置默认值
const props = withDefaults(defineProps<Props>(), {
  visible: false,
  options: () => []
})
</script>
```

### 5.2 Emits 类型

```vue
<script setup lang="ts">
// 定义 Emits
const emit = defineEmits<{
  // 无参数
  close: []
  // 单参数
  change: [value: string]
  // 多参数
  select: [item: OptionItem, index: number]
}>()

// 使用
emit('close')
emit('change', 'value')
emit('select', item, 0)
</script>
```

### 5.3 Ref 类型

```vue
<script setup lang="ts">
import { ref } from 'vue'

// 基础类型
const count = ref<number>(0)
const name = ref<string>('')

// 对象类型
const tenant = ref<Tenant | null>(null)

// 数组类型
const list = ref<Tenant[]>([])

// 组件 ref
const formRef = ref<InstanceType<typeof CompForm> | null>(null)
</script>
```

---

## 六、Store 类型定义

### 6.1 State 类型

```typescript
// store/modules/Tenant.ts
import { defineStore } from 'pinia'

interface TenantState {
  list: Tenant[]
  detail: Tenant | null
  loading: boolean
  filters: TenantFilters
}

interface TenantFilters {
  status: string
  keyword: string
}

const useTenantStore = defineStore('tenant', {
  state: (): TenantState => ({
    list: [],
    detail: null,
    loading: false,
    filters: {
      status: '',
      keyword: ''
    }
  }),

  actions: {
    setList(data: Tenant[]) {
      this.list = data
    },

    setDetail(data: Tenant | null) {
      this.detail = data
    }
  }
})
```

---

## 七、工具函数类型

### 7.1 泛型函数

```typescript
// utils/request.ts

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, any>
  showLoading?: boolean
}

export const request = async <T>(options: RequestOptions): Promise<T> => {
  // 实现
}

// 使用
const data = await request<Tenant>({ url: '/api/tenant/1' })
```

### 7.2 类型守卫

```typescript
// utils/validate.ts

// 类型守卫
function isTenant(obj: any): obj is Tenant {
  return obj && typeof obj.id === 'number' && typeof obj.name === 'string'
}

// 使用
if (isTenant(data)) {
  console.log(data.name)  // TypeScript 知道 data 是 Tenant 类型
}
```

---

## 八、常见类型模式

### 8.1 可选属性

```typescript
// Partial - 所有属性可选
type TenantUpdate = Partial<Tenant>

// Pick - 选取部分属性
type TenantBasic = Pick<Tenant, 'id' | 'name' | 'phone'>

// Omit - 排除部分属性
type TenantCreate = Omit<Tenant, 'id' | 'createTime' | 'updateTime'>
```

### 8.2 联合类型

```typescript
// 状态联合
type Status = 'pending' | 'success' | 'error'

// 根据状态返回不同类型
type Result<T> =
  | { status: 'success'; data: T }
  | { status: 'error'; message: string }
```

### 8.3 映射类型

```typescript
// 表单字段配置
type FormItemMap<T> = {
  [K in keyof T]: {
    type: 'input' | 'picker' | 'date'
    label: string
    required?: boolean
    placeholder?: string
  }
}

// 使用
const tenantFormMap: FormItemMap<TenantForm> = {
  name: { type: 'input', label: '姓名', required: true },
  phone: { type: 'input', label: '手机号', required: true },
  idCard: { type: 'input', label: '身份证', required: true }
}
```

---

## 九、检查清单

- [ ] tsconfig.json 配置正确
- [ ] API 响应有类型定义
- [ ] 业务模型有类型定义
- [ ] 组件 Props 使用 interface 定义
- [ ] Emits 使用泛型定义
- [ ] ref 指定类型
- [ ] 避免使用 `any`（除非确实需要）
- [ ] 工具函数有参数和返回类型
