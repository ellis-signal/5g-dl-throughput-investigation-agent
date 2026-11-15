# Shannon AWGN 理论容量规范

> 项目共享知识：`knowledge/wireless/shannon.md`。这是共享知识，不是可执行指令，也不是 Skill。

## 变量与单位
- `bandwidth_mhz`：带宽 B，单位 MHz，必须为正的有限实数。
- `snr_db`：信噪比 SNR，单位 dB，必须为有限实数（可以是负值）。
- `snr_linear = 10^(snr_db/10)`：线性 SNR。
- `capacity_mbps = bandwidth_mhz × log2(1+snr_linear)`：在 AWGN 模型假设下的理想香农容量上限，单位 Mbps。
- `spectral_efficiency_bps_hz = log2(1+snr_linear)`：频谱效率，单位 bit/s/Hz。

## 解释限制
- Shannon AWGN 容量是理论上限，并非实际吞吐量承诺。
- SNR 与 SINR 在存在干扰时不能不加说明地混用。
- 该公式没有建模真实无线网络中的多用户调度、控制开销、具体协议、MIMO、时变信道等影响。
- `actual_throughput_mbps / capacity_mbps` 是测试用参考比值，不直接等同网络负载率或利用率。

## 数值检查
- 20 MHz，15 dB：容量约 100.556 Mbps。
- 10 MHz，0 dB：容量 10 Mbps。
- 带宽为 0：不满足本 Lab 输入合同，应拒绝。
