# 虚拟化技术原理

## Type1 vs Type2

| 类型 | 说明 | 示例 |
|:---|:---|:---|
| Type1（裸机型） | Hypervisor 直接运行在硬件上 | VMware ESXi, KVM, Xen |
| Type2（宿主型） | Hypervisor 运行在操作系统上 | VirtualBox, QEMU |

## CPU 虚拟化

- Intel VT-x/AMD-V：硬件辅助虚拟化
- 全虚拟化：不需要修改 Guest OS
- 半虚拟化：Guest 需修改内核，性能更好

## 内存虚拟化

- EPT（Intel Extended Page Tables）：硬件辅助内存虚拟化
- 影子页表：纯软件实现（性能较差）

## IO 虚拟化

| 方式 | 性能 | 复杂度 | 场景 |
|:---|:---:|:---:|:---|
| QEMU 模拟 | 低 | 低 | 兼容性优先 |
| virtio | 中 | 中 | 通用场景 |
| VFIO 直通 | 高 | 高 | 高性能场景 |
| SR-IOV | 高 | 中 | 网卡直通 |
