# UI/UX
- 用户偏好中文界面的UI工具，并在颜色/色板相关开发中关注WCAG无障碍对比度标准，支持hex/rgb/hsb/hsl多种颜色格式切换。
- 用户希望助手连接其Figma账号参考设计稿进行开发，要求视觉布局与Figma完全一致，但使用自定义数据替换占位数据。
- 用户偏好极简主义风格的UI设计。
- 用户要求代码预览效果同时支持并展示light和dark mode。
- 颜色输入框需智能处理粘贴操作，自动过滤重复的#前缀以防截断错误。
- Landing page中特定卡片标题与操作按钮间需保留两行空格以增强视觉留白效果。

# DevOps
- 用户希望通过GitHub来发布和部署可直接访问的网站。

# Design System
- 用户偏好采用包含hex和rgba字段的结构化JSON格式定义UI色板数据，并明确区分自定义色板与代码原有灰色色板。
- 用户要求使用指定的多色阶dark mode色板数据训练generate_brand_palette.py模型，专门用于生成dark mode的品牌色色板，以区分light mode和dark mode的相反特性。
