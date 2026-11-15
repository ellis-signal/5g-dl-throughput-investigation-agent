# 5G 小区下行吞吐率异常调查 Agent

入口是 `/agent.html`，也可使用命令行。项目使用十个模拟案例。主页保留了组员编写的早期规则账本界面。
代码与报告整理有 Codex 辅助，实验保留了工具实际返回和模型原始输出。

## 启动

本项目验证环境为 Windows、Python 3.12、llama.cpp b11723 和 Qwen3-4B-Q4_K_M。Python 依赖可用 `python -m pip install -r requirements.txt` 安装。模型和服务程序在压缩包外，来源为 llama.cpp 发布页和 Hugging Face 的 Qwen/Qwen3-4B-GGUF 仓库。模型服务需支持 OpenAI 兼容的 function calling。

```powershell
llama-server.exe -m Qwen3-4B-Q4_K_M.gguf --host 127.0.0.1 --port 18110 -c 8192 -ngl 99 --jinja
python -m uvicorn backend.app:app --host 127.0.0.1 --port 18765
```

第一条在独立终端运行。按本地文件位置调整路径。没有支持的 GPU 时可使用 CPU 版并设置 `-ngl 0`。浏览器打开 http://127.0.0.1:18765/agent.html。若模型地址或名称不同，启动应用前设置 `MODEL_URL`（完整 chat/completions 地址）及 `MODEL_NAME`。后端端口与模型端口分别为 18765 和 18110。

```powershell
python -X utf8 src/wireless_lab/agent.py --case NR-CELL-1002 --mode D --output trace.json
python -X utf8 -m unittest discover -s tests
python -X utf8 tests/evaluate_project.py
```

## 评测与文件

- `data/evaluation_cases.json` 为十个窗口汇总案例及其预设标签。1001 至 1004 来自项目组已有原始模拟数据，每窗口24个样本。1005、1006是PRB缺失变体。1007至1010为独立构造的汇总案例。
- `results/evaluation.csv` 与 `results/traces/` 保留初版六例对照。`results/final/` 保存最终对照和40条配置结果，其中D复用C的调用结果。复现脚本默认写入 `results/reproduction/`。
- A直接接收KPI汇总，B开放三个工具，C在B上加载诊断Skill，D对C实际返回的KPI和窗口差值应用后端证据核对。D是网页默认配置，原始模型回答仍在 `model_answer`。缺少成功的查询或比较工具结果时，D返回证据不足。
- `evaluate_project.py` 统计标签匹配及同时成功调用查询和比较工具的比例，另记录成功调用次数和模型运行时间。D继承C的模型耗时。温度0、关闭思考、最多六轮，单次实测结果可能随模型服务版本和硬件变化。
- `skills/5g-dl-investigation/SKILL.md` 是实际加载的专业提示。阈值为模拟教学规则。系统使用预先对齐的汇总窗口，结论表示核查优先级。独立审计功能复算早期账本，最终Agent的证据核对由 `review.py` 执行。香农参考是理想条件计算。
