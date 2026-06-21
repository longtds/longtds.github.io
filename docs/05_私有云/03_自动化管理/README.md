# 自动化管理

## OpenTofu/Terraform

OpenTofu 是 Terraform 的开源分支，兼容 HCL。

```hcl
# OpenStack 资源编排示例
resource "openstack_compute_instance_v2" "web" {
  name      = "web-${count.index}"
  image_id  = data.openstack_images_image_v2.ubuntu.id
  flavor_id = "m1.medium"
  count     = 3

  network {
    uuid = openstack_networking_network_v2.internal.id
  }
}
```

## Ansible

```yaml
# Playbook 示例
- name: Deploy web server
  hosts: webservers
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present

    - name: Start nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
```
