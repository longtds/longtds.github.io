# 基础设施即代码

## Ansible

```yaml
# Playbook 结构
- name: Configure web server
  hosts: webservers
  become: yes
  vars:
    nginx_port: 80
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
    - name: Copy config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: restart nginx
  handlers:
    - name: restart nginx
      systemd:
        name: nginx
        state: restarted
```

## OpenTofu

```hcl
# 声明式资源管理
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  tags = {
    Name = "web-server"
  }
}
```

## 声明式 vs 指令式

| 范式 | 做法 | 优点 | 缺点 |
|:---|:---|:---|:---|
| 指令式 | 写步骤（先 A 后 B） | 灵活 | 易出错，幂等差 |
| 声明式 | 描述期望状态 | 幂等，可审计 | 学习曲线 |
