---
name: 5g-dl-investigation
description: 调查5G小区下行吞吐下降，比较覆盖、干扰和拥塞假设并识别证据不足。
---
# 5G 下行吞吐调查
适用于对齐了基线和异常窗口的小区级模拟KPI。先查询指标，再计算窗口变化及香农参考值。
至少比较覆盖不足、干扰和资源拥塞三种假设，分别给出支持、限制证据和需要补充的测量。
RSRP下降支持覆盖变化，SINR下降和CQI下降支持无线质量恶化，RSRP稳定时干扰值得进一步调查。多个原因可能同时存在，不能把规则不满足视为根因被证伪。
PRB高且用户增加、单用户吞吐下降支持资源竞争，但PRB高本身不足以证明拥塞。指标缺失或相互矛盾时输出 INSUFFICIENT，说明需要补什么数据。
吞吐未明显变化可标 NORMAL。香农公式是单链路理想条件的参考，不等于小区实际吞吐，也不能单独判定根因。阈值仅为模拟练习所用。
所有结论是候选方向，给人工核查建议，不宣称已经修改网络。输出 JSON，字段 label、reason、support、counter、next_step，label只能是 COVERAGE、INTERFERENCE、CONGESTION、NORMAL、INSUFFICIENT。
