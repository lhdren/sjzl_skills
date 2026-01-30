# 学术写作规范详解

## 一、学术语言规范

### 1.1 客观陈述原则

**推荐表达**：
```markdown
✅ The experimental results demonstrate that...
✅ This approach shows significant improvement...
✅ The data suggest a correlation between...
✅ We observe that the proposed method...
```

**避免表达**：
```markdown
❌ Our method is definitely the best...
❌ It is absolutely clear that...
❌ Without a doubt, this proves...
❌ Everyone agrees that...
```

### 1.2 谨慎断言 (Hedging)

学术写作需要谨慎，避免过于绝对：

| 绝对表达 | 谨慎表达 |
|----------|----------|
| proves | suggests, indicates |
| always | often, frequently |
| never | rarely, seldom |
| perfect | excellent, superior |
| all | most, many |

**示例**：
```markdown
❌ "This proves that our method is superior."
✅ "The results suggest that our method achieves competitive performance."
```

### 1.3 第一人称使用

现代学术写作中，适当使用第一人称可以接受：

```markdown
✅ "We propose a novel approach..."
✅ "Our contributions include..."
✅ "In this work, we investigate..."
```

但避免过度使用：
```markdown
❌ "I think...", "I feel...", "I believe..."
```

---

## 二、段落写作技巧

### 2.1 段落结构模板

**标准四段式结构**：

```markdown
[主题句] - 明确段落的中心思想
  ↓
[支持证据] - 提供数据、引用、实例
  ↓
[分析讨论] - 解释证据的含义
  ↓
[过渡句] - 连接到下一段
```

**示例**：

```markdown
[主题句] 深度学习在医学影像分析中取得了显著进展。

[支持证据] 在CCTA冠状动脉分割任务中，U-Net及其变体[12,15]将Dice系数
从0.78提升至0.89。此外，Transformer-based方法[18]进一步将性能提升至0.92。

[分析讨论] 这些改进主要归因于更深层的网络结构和更有效的注意力机制，
使得模型能够更好地捕捉复杂的解剖结构特征。

[过渡句] 然而，这些方法在处理病理变化时仍面临挑战，如下一节所述。
```

### 2.2 段落长度

- **推荐**: 100-200字
- **过短**: < 50字（缺乏充分论证）
- **过长**: > 300字（读者难以跟随）

### 2.3 段落过渡

**过渡词和短语**：

| 功能 | 表达 |
|------|------|
| 递进 | Furthermore, Moreover, In addition |
| 转折 | However, Nevertheless, Conversely |
| 因果 | Therefore, Thus, Consequently |
| 对比 | In contrast, On the other hand |
| 总结 | In summary, To conclude |

---

## 三、引用规范

### 3.1 引用时机

**必须引用**：
- 陈述事实/数据
- 描述他人工作
- 使用已知结论
- 引用方法/公式

**无需引用**：
- 公共知识（如"地球是圆的"）
- 自己的原始贡献

### 3.2 引用格式

```markdown
# 单一引用
Recent studies [15] have shown...

# 多引用
Several approaches [1, 2, 5, 8] have been proposed...

# 连续引用
Early works [1-5] focused on...

# 作者提及
Smith et al. [12] proposed...

# 具体陈述
According to [15], the performance...
```

### 3.3 引用位置

| 位置 | 示例 |
|------|------|
| 句末 | ...achieves 95% accuracy [15]. |
| 句中 | Smith [15] demonstrated that... |
| 多处 | Both [12] and [15] reported... |

---

## 四、图表规范

### 4.1 图表编号

- 按出现顺序连续编号
- 章节内编号：Fig. 1, Fig. 2 / Table 1, Table 2
- 全文编号：Figure 1, Figure 2 / Table 1, Table 2

### 4.2 图表标题

```markdown
# 图标题（放在图下方）
Fig. 1. Overall architecture of the proposed method.

# 表标题（放在表上方）
Table 1. Dataset Statistics
```

### 4.3 图表引用

在正文中引用图表：
```markdown
As shown in Fig. 1, the proposed method...
The results in Table 2 demonstrate that...
```

---

## 五、数字与单位规范

### 5.1 数字格式

| 情况 | 格式 | 示例 |
|------|------|------|
| 小数点前非零 | 保留2位 | 0.89, 12.34 |
| 小于1 | 加0 | 0.05 (不是 .05) |
| 大数 | 使用逗号 | 1,234,567 |
| 范围 | 使用~或to | 10~20, 10 to 20 |
| 约等于 | ≈ | ≈100 |

### 5.2 百分比

```markdown
✅ 95.2% (留一位小数)
✅ 95% (整数即可时)
❌ 95.2341% (精度过高)
```

### 5.3 单位

```markdown
# 数字与单位间加空格
✅ 100 MB
✅ 2.5 GHz
❌ 100MB
✅ 50 ms (时间)
✅ 32 × 32 (尺寸，用×不是x)
```

---

## 六、常见语法问题

### 6.1 主谓一致

```markdown
❌ The data shows... (data是复数)
✅ The data show...

❌ Each method have... (each是单数)
✅ Each method has...
```

### 6.2 时态使用

| 章节 | 时态 | 示例 |
|------|------|------|
| Introduction | 现在/过去 | Recent studies show... |
| Related Work | 过去 | Smith [15] proposed... |
| Method | 过去 | We implemented... |
| Results | 过去 | The model achieved... |
| Discussion | 现在 | These results suggest... |

### 6.3 冠词使用

```markdown
❌ "the proposed method achieves..." (首次提到)
✅ "a proposed method achieves..." 或 "our proposed method achieves..."

✅ "The proposed method [前面提到的] achieves..."
```

---

## 七、写作检查清单

### 内容检查
- [ ] 每个段落有明确主题句
- [ ] 每个观点有证据支持
- [ ] 逻辑连贯，论证充分
- [ ] 没有未定义的术语/缩写

### 语言检查
- [ ] 无语法错误
- [ ] 时态一致
- [ ] 主谓一致
- [ ] 冠词正确

### 格式检查
- [ ] 引用格式统一
- [ ] 图表编号连续
- [ ] 单位格式规范
- [ ] 数字格式一致
