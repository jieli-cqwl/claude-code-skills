Google工程师给的《Gemini 3提示词最佳实践指南》
昨晚在社区论坛刷到了Philipp（Google DeepMind的开发工程师，负责开发者体验和开发者关系方面的工作）的一篇Blog，内容是作者分享自己关于Gemini 3提示词工程的最佳实践经验，觉得颇为受用，我把作者的分享大概整理了一下，一起来学习下如何从和AI“聊天”转向真正的“提示词工程”。

图片
五大核心原则

在构建任何提示词之前，请遵循以下基础逻辑：

1、指令要精准

拒绝废话。不要使用“请你帮我...”或“这对我很重要”等情感修饰语。直接、清晰地陈述你的目标。Gemini 3 对简洁明了的命令式指令反应最佳。

2、保持一致性

提示词应具备像代码一样的规范性。

统一结构：全篇统一使用 XML 标签（如 ）或 Markdown 标题。

定义术语：如果任务中包含模棱两可的词汇，必须在开头明确定义它的含义。

3、多模态融合

Gemini 3 是原生多模态模型。不要将图像或视频视为“附件”，它们和输入的文本一样重要。

明确引用：在指令中明确指向特定的模态（例如：“结合视频中的动作和下方的文本描述进行分析...”），强制模型进行跨模态综合推理，而非单独处理。

4、约束前置

锚定推理起点。 将所有的行为约束（如“不准使用表情包”、“必须输出 JSON”）和角色定义放在提示词的最顶端（System Prompt）。这能作为模型推理的“锚点”，防止在生成回答的过程中跑偏。

5、长上下文处理

当处理长文档或大量数据时：

指令后置：将具体要执行的任务指令放在大量数据的末尾。

桥接语句：在数据结束和指令开始之间，使用过渡句（如“基于上述提供的所有信息，请执行……”）来重新唤醒模型的注意力。

三大关键实践

这是提升输出质量的进阶技巧，将简单的问答转化为深度的思维过程。

1、推理与规划

不要让模型直接给出答案，这往往会导致AI幻觉或得到一些比较肤浅的答案。我们要强制让AI模型先“思考”：

显式拆解：要求模型在回答前，先将大目标拆解为子任务，并检查输入信息是否完整。

自我更新的任务清单：让模型在输出中创建一个动态的 TODO 列表。如：

Create a TODO list to track progress:

- [ ] Primary objective
- [ ] Task 1
- [ ] Task 2
....
- [ ] Review

这能帮助模型在长任务中保持状态，不会遗漏步骤。

自我批判：要求模型在输出最终响应前，先自己进行校验审核。如：

Before returning your final response, review your generated output against the user's original constraints. 
译：在给出最终回复之前，请对照用户最初设定的限制条件，再次检查您生成的输出内容。
1. Did I answer the user's intent, not just their literal words?  
译：我是否真正满足了用户的意图，而非仅仅遵循了他们字面上的意思呢？
2. Is the tone authentic to the requested persona? 
译：这种语气是否符合所要求的个性特征？
3. If I made an assumption due to missing data, did I flag it? 
译：如果因为我所获取的数据不足而做出了某种假设，我是否已经对此进行了标注说明了呢？
2、结构化提示

像写软件一样写提示词。使用清晰的标记语言来界定边界，帮助模型区分哪部分是指令和哪部分是数据。

如 XML 或者 Markdown 风格：

XML 风格: 
<rules>在此定义绝对规则</rules>
<context>在此放入背景资料</context>
<planning_process>在此展示思考过程</planning_process>

Markdown 风格：使用 # Identity（身份）、# Constraints（约束）等标题。
注意：选择一种格式后记得全篇保持一致，不要混用。

3、智能体工具使用

当你把 Gemini 3 作为能够调用工具（如搜索、代码解释器）的自主智能体（Agent）时，需要增强它的韧性：

坚持指令。明确写入规则：“必须持续工作直到问题被完全解决。”如果工具调用失败或报错，模型应分析错误原因并尝试替代方案（如换一个搜索词），绝对不能直接放弃或把报错抛回给用户。

预计算反思。在模型调用任何工具之前，强制它进行一键三连的思考：我为什么要调用这个工具？我期望获取什么具体数据？这个数据如何直接帮助解决用户的问题？

场景应用模版策略

针对特定任务，我们需要让AI变成遵守SOP（标准作业程序）的专业人士，通过 1, 2, 3, 4 ...的步骤，强迫 AI 在输出最终结果之前，必须先经过特定的处理流程。Philipp也给出了一些具体场景的策略建议：

研究与分析（强制先分解问题、再独立分析、最后合并结论并强制引用来源，防止AI一上来就胡编乱造一个结论。）

1. Decompose the topic into key research questions
2. Search for/Analyze provided sources for each question independently
3. Synthesize findings into a cohesive report
4. CITATION RULE: If you make a specific claim, you must cite a source. If no source is available, state that it is a general estimate. Every claim must be immediately followed by a reference [Source ID]

创意写作（明确受众读者，为了显得自然，明确需要禁用“行业黑话”等）

1. Identify the target audience and the specific goal (e.g., empathy vs. authority).
2. If the task requires empathy or casualness, strictly avoid corporate jargon (e.g., "synergy," "protocols," "ensure").
3. Draft the content.
4. Read the draft internally. Does this sound like a human or a template? If it sounds robotic, rewrite it.
解决问题（多重方案对比，要求模型先找出标准解决方案，再找出最佳解决方案，并解释为什么最佳解决方案更好）

1. Restate the problem in your own words.
2. Identify the "Standard Solution."
3. Identify the "Power User Solution" (Is there a trick, a specific tool, or a nuance most people miss?).
4. Present the solution, prioritizing the most effective method, even if it deviates slightly from the user's requested format.
5. Sanity check: Does this solve the root problem?
教学内容（AI容易用复杂的术语解释复杂的概念，强迫 AI 必须“说人话”，并像老师一样确认学生是否听懂了）

1. Assess the user's current knowledge level based on their query.
2. Define key terms before using them.
3. Explain the concept using a relevant analogy.
4. Provide a "Check for Understanding" question at the end.
对于企业或需要批量生产内容的人来说，这些模板其实就是 SOP（标准作业程序）。它保证了无论 AI 产出的内容中，我们所关心的那些核心要素，不会出现时好时坏的情况。

总结

总的来说，AI提示词没有完美的模板或上下文结构。上下文工程是一个经验性的过程，而非固定的语法。我们需要根据的具体用例不断进行迭代、测试和改进。