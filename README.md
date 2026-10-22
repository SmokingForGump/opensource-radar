# OpenSource Radar

有证据、有观点、有尝试路径的开源科技杂志。中文优先，兼顾产品启发、工程实践、生活发现与知识管理。

目标站点：https://smokingforgump.github.io/opensource-radar/

## 阅读与发布

每周四精选；每两周一次 Monthly 深研。只有通过事实复核、隐私门禁和公共 CI 的内容才会发布。没有实际运行项目时，会明确标注。初期没有历史数据时，不展示虚构趋势。

## 本地构建

使用 Python 3.9 或更新版本，无需安装第三方依赖：

```sh
python3 -m unittest discover -s tests -v
python3 build.py
```

公开文章位于 content/issues，配套文件哈希位于 content/manifests。严格公开契约见 radar_contract.py。研究凭证不保存在本仓库。

Pages 使用 GitHub Actions；仅部署任务具有 Pages 写入权限。所有外部 Action 固定到已核实的提交，Dependabot 每周提出更新。正式采用依赖锁文件前保持 SHA 固定。

## 内容与更正

研究由 AI 辅助，事实与引用仍可能有误。欢迎附原始来源提交更正，请勿公开任何个人信息或密钥。第三方项目及材料遵循原作者许可证；没有确认许可证的项目不标记为可商用。

当前未授予本站代码与原创文章统一的再许可；后续选择许可时将明确范围。
