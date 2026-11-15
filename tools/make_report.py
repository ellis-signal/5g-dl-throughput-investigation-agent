from pathlib import Path
from io import BytesIO
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from xml.sax.saxutils import escape
root=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
body=ParagraphStyle('body',fontName='STSong-Light',fontSize=11,leading=18,spaceAfter=9,wordWrap='CJK')
title=ParagraphStyle('title',parent=body,fontSize=18,leading=28,alignment=TA_CENTER,spaceAfter=20)
heading=ParagraphStyle('head',parent=body,fontSize=15,leading=23,textColor=colors.black,spaceBefore=5,spaceAfter=12)
small=ParagraphStyle('small',parent=body,fontSize=9,leading=14)
def p(t,style=body):return Paragraph(escape(t).replace('\n','<br/>'),style)
def img(path,w,h):
    source = PILImage.open(root/path).convert('L')
    data = BytesIO()
    source.save(data, format='PNG')
    data.seek(0)
    return Image(data,width=w,height=h,kind='proportional')
def table(data,widths):
 t=Table([[p(str(x),small) for x in row] for row in data],colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#777777')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]));return t
def footer(c,doc):
 c.setFont('STSong-Light',9);c.setFillColor(colors.grey);c.drawRightString(190*mm,15*mm,str(doc.page))

import csv
import json
from statistics import mean
from reportlab.graphics.shapes import Drawing, Rect, String, Line

rows = list(csv.DictReader((root/'results/final/evaluation.csv').open(encoding='utf-8-sig')))
groups = {k: [r for r in rows if r['mode']==k] for k in 'ABCD'}
scores = {k: sum(int(row['correct']) for row in group) for k, group in groups.items()}
names = dict(A='直接询问', B='模型和工具', C='工具与Skill', D='加证据核对')
S = []


def add(*items):
    S.extend(items)


def section(title_text):
    add(p(title_text, heading))


def paragraphs(*items):
    add(*(p(t) for t in items))


def caption(t):
    add(p(t, ParagraphStyle('caption', parent=small, alignment=TA_CENTER)))


def chart():
    d = Drawing(425, 150)
    for i, (mode, value) in enumerate(scores.items()):
        y = 116 - i*30
        d.add(String(4,y,mode+' '+names[mode],fontName='STSong-Light',fontSize=11))
        d.add(Rect(100,y-3,value*27,14,fillColor=colors.HexColor('#dddddd'),strokeColor=colors.black))
        d.add(String(105+value*27,y,f'{value}/10',fontSize=10))
    return d


def architecture():
    d = Drawing(430, 105)
    labels = ['工程师输入', '模型和Skill', '工具与数据', '证据核对', '调查输出']
    for i, label in enumerate(labels):
        x = i*86
        d.add(Rect(x,48,72,27,fillColor=colors.white,strokeColor=colors.black))
        d.add(String(x+36,58,label,textAnchor='middle',fontName='STSong-Light',fontSize=10))
        if i<4:
            d.add(Line(x+72,62,x+86,62))
            d.add(Line(x+82,65,x+86,62))
            d.add(Line(x+82,59,x+86,62))
    d.add(String(215,24,'工具回包送回模型，并随最终结果存入调查轨迹',textAnchor='middle',fontName='STSong-Light',fontSize=10))
    return d


add(Spacer(1,42*mm),p('5G 小区下行吞吐率异常调查 Agent',title),
    p('《人工智能的网络应用》课程综合项目',ParagraphStyle('sub',parent=body,alignment=TA_CENTER,fontSize=13)),
    Spacer(1,20*mm),
    Spacer(1,14*mm))
section('摘要')
paragraphs(f'本项目面向5G无线网络优化工程师，使用模拟小区指标，比较覆盖变化、无线干扰和资源竞争等调查假设。模型执行工具调用，后端核对量化证据并保留原始记录。四种配置在十个模拟案例中分别匹配{scores["A"]}、{scores["B"]}、{scores["C"]}和{scores["D"]}个预设标签。加入证据核对后，系统能够识别复合线索和缺失数据。结果适用于本次模拟案例。')
add(p('关键词　5G　下行吞吐率　工具调用　证据核对',small),PageBreak())

section('一、项目背景与问题定义')
paragraphs(
'当某个小区出现网速投诉时，工程师首先需要确认小区下行吞吐率是否真的异常，再决定去查射频、负荷或其他环节。吞吐率随流量和无线环境变化，单个时点的数值缺乏上下文。同一现象可能来自覆盖变化、干扰增加、资源竞争，也可能与回传或业务端有关。对应的后续测量不同，选错第一条线索会增加排查时间。',
'例如，模拟事件 NR-CELL-1002 的下行平均吞吐从472.21 Mbps降至96.44 Mbps，同时SINR下降，PRB利用率仅小幅变化。若只看用户投诉，可以提出拥塞假设。若进一步对比基线和事发窗口，负荷变化很难单独解释这次幅度，还应核查信道质量和干扰线索。本项目把这种查看、比较和解释的过程整理成一次可追溯的调查。',
'Agent的输入包括小区编号和调查问题，输出包括可查的原始指标、计算结果、逐个假设的检查项和下一步测量建议。当前数据包含覆盖、干扰、拥塞、正常、复合和缺失几种情形。系统允许在缺少观测时给出证据不足，也允许多个方向同时保留。模拟数据与诊断阈值用于课程演示，程序仅在本地读取数据。',
'四个原始小区由固定种子的生成脚本构造，每个基线和事发窗口均包含二十四条按小时的样本。窗口以对应时段对比，查询工具展示已聚合的数据。后续增加的案例直接以窗口统计值构造，专门用于测试误判边界和字段缺失。两类数据的来源在README中标明。')
add(PageBreak())

section('二、系统架构与 Agent 设计')
paragraphs(
'工程师从网页选择小区并输入问题，也可在命令行指定案例。FastAPI将输入传给单Agent，程序按配置向本机模型发送问题、工具描述和诊断Skill。模型选择工具和填写参数，服务端只执行已注册的工具，并核对请求中的编号与本次调查一致。工具返回作为消息交还模型，模型可据此继续调用，直到输出答案或用尽调用轮次。',
'每次成功或失败的调用都记录工具名、参数和返回值。后端核对只读取本次工具真正成功返回的查询和窗口对比数据。若其中一项缺失，结果为证据不足。模型原始回答完整保留，通过轨迹可以检查模型是否使用了这些信息，也能对照后端为什么给出了不同的调查方向。',
'选用本机Qwen3-4B是为了复用可在实验电脑运行的环境。轻量Agent直接使用OpenAI兼容接口，能明确记录每次模型和工具交换的数据。规则核对独立于自然语言输出，适合测试缺失、冲突和数值临界情形。前端呈现工具返回、证据编号和建议，模型服务不可用时通过接口返回失败。')
add(architecture())
caption('图1 系统架构和典型执行流程')
paragraphs('实际执行依次经过输入、模型取证、回包反馈、判断与核对、证据呈现。主要流程的命令行和网页入口使用相同的运行函数。原型页面保留既有账本及独立复算功能，最终调查入口使用带证据核对的配置。')
add(PageBreak())

section('三、工具、专业 Skill 和证据核对')
caption('表1 模型可以发起的工具调用')
add(table([['工具','输入','功能和返回'],['get_kpi','小区编号','带宽、基线窗口及事发窗口统计值'],['compare_windows','小区编号','指标变化量、吞吐与用户数相对变化、缺失字段'],['calculate_capacity','小区编号','用事发SINR和带宽计算理想香农参考值']],[37*mm,28*mm,93*mm]))
paragraphs(
'查询限定在十个模拟案例。窗口比较用事发值减基线值，PRB和BLER差值以百分点表示，吞吐和用户数相对变化以基线为分母。空值保留，基线为零时相对变化无定义。容量工具先将dB换成线性比，再应用香农公式。缺SINR时返回工具错误。一条链路的理想参考值只能提供量级参照，实际聚合吞吐还与调度及业务需求等因素有关。',
'5G诊断Skill将基线对比、候选假设、反证和下一步测量写成工作顺序。C和D加载同一份文件。它提示模型在信号变化、无线质量和负荷三个维度取证，并对缺失字段保持谨慎。实验保留C的实际答案，从而可以单独观察提示以及后续核对的作用。',
'后端把八项数值编号为E1至E8，再为每个假设记录支持、削弱和缺失。例如，覆盖方向核对RSRP及SINR是否明显下降，干扰方向核对相对稳定的RSRP及下降的SINR和CQI，并结合BLER，资源竞争方向核对事发和增量PRB及用户数增长。所有阈值均为本实验的教学规则。',
'程序先用10%下降门槛判断事件是否达到异常条件。达到门槛后，关键字段缺失或规则命中多个方向时给出证据不足。观察值不满足某个检查条件会削弱该教学假设。工程师仍需看邻区、分时测量或其他业务指标。')
add(Preformatted(
    "delta[key] = round((current / base - 1) * 100, 2) if base and current is not None else None",
    ParagraphStyle('code', fontName='Courier', fontSize=7.5, leading=13)))
caption('代码1 窗口比较工具的相对变化计算，摘自 agent.py')
paragraphs('调用入参为含 case_id 的对象，返回以指标键名索引的数值字典。代码1在缺少当前值或基线为零时返回空值，证据核对因此可以保留观测缺口。')
add(PageBreak())

section('四、真实运行实例')
paragraphs(
'将NR-CELL-1002作为代表案例，输入调查小区下行吞吐下降并比较覆盖、干扰及拥塞。模型发出工具请求，参数为 case_id=NR-CELL-1002。get_kpi返回两个窗口的汇总，compare_windows计算吞吐下降79.58%、RSRP上升0.41 dB、SINR下降16.35 dB。独立香农计算以100 MHz和1.695 dB为输入，结果约130.88 Mbps。',
'本次核对中，E2显示RSRP基本稳定，削弱覆盖恶化假设。E3和E4分别记录SINR下降16.35 dB和CQI下降6.81，E8的BLER上升15.004个百分点，支持进一步核查干扰。E5显示事发PRB约53.83%，E7的用户增长仅3.64%，两者均削弱资源竞争假设。因此系统将干扰线索列为优先方向，建议对照邻区同窗SINR和BLER，并检查可取得的干扰测量。',
'同一案例的最终对照中，C的模型原始答案给出了拥塞标签。D使用同一次工具回包核对后得到干扰方向。该轨迹展示了即使工具正确执行，模型仍可能忽略反面证据，也展示了后端修正所依据的具体数值。完整回包和模型答案见最终结果目录中对应的轨迹。')
add(PageBreak())
section('四、真实运行截图')
add(img('docs/screenshots/final-tools.png',155*mm,90*mm))
caption('图2 调查输入、实际工具调用与返回数据')
add(Spacer(1,4*mm),img('docs/screenshots/final-result.png',155*mm,79*mm))
caption('图3 同一次调查的指标证据、假设核对与后续建议')
paragraphs('两图来自同一次本地浏览器运行。工具的完整返回和模型输出见 results/final/traces 中的 NR-CELL-1002 对照轨迹。浏览器演示和保存的评测是两次独立执行，二者使用同一合成案例和证据核对逻辑。')
add(PageBreak())

section('五、实验设计和结果')
paragraphs(
'十个模拟案例覆盖覆盖变化、干扰、资源竞争、正常波动、缺少PRB、复合线索、指标不足和临界吞吐下降。其中1005、1006由已有案例移除PRB得到，1007至1010是独立构造的窗口汇总。案例预设标签表示合适的优先核查方向，标签与研究者对模拟场景的设定对应。',
'四组使用同一基础模型、温度和问题。A直接接收相同的窗口汇总，B开放工具，C增加诊断Skill，D在C的实际工具结果上核对证据。D复用C本次的模型与工具调用，因此C到D的变化可以归因于增加的后端核对。各案例每种模型配置运行一次，原始输出、工具调用与评测表一同留存。',
'标签匹配率按预设标签计算。关键取证成功率要求同一案例中KPI查询和窗口比较均成功。后者衡量数据链路，即使两个工具调用都成功，仍需另外检查最终判断是否正确。D的耗时沿用C的模型链路记录。')
caption('表2 四组对照实验结果')
data = [['组别','标签匹配','关键取证','平均模型链路耗时']]
for k, group in groups.items():
    calls = '不适用' if k=='A' else f"{sum(int(r['required_tools']) for r in group)}/10"
    data.append([k+' '+names[k],f'{scores[k]}/10',calls,f"{mean(float(r['seconds']) for r in group):.2f} 秒"])
add(table(data,[43*mm,30*mm,33*mm,52*mm]),Spacer(1,4*mm),chart())
caption('图4 十个模拟案例的标签匹配数')
add(PageBreak())

section('五、失败分析与实验局限')
paragraphs(
'在1001中，B和C都调用了KPI查询、窗口比较和容量计算，工具选择相同。B把PRB利用率及活跃用户数下降解读为拥塞。C转向检查无线指标，却把RSRP描述为稳定，实际比基线下降16.19 dB。因此Skill改变了模型的解释重点，该例仍然误判。对应原始回答见B和C两条1001轨迹。',
f'最终对照中A、B、C的模型原始答案匹配数分别为{scores["A"]}、{scores["B"]}、{scores["C"]}。加入工具后，模型能取得所需数据，但标签匹配并未稳定提升。本次实验没有观察到仅加入Skill即可改善判断的证据。将指标和结论之间的关系交由明确的核对规则处理后，D匹配了{scores["D"]}个案例。',
'1007同时注入了覆盖和负荷信号，事发RSRP比基线低11 dB，SINR下降9 dB，事发PRB为96%，活跃用户从39增加到91。C给出了拥塞标签，漏掉同时存在的覆盖线索。D保留两个方向并提示分时或分区复核。1008有明显吞吐下降，但当前无线质量和负荷指标不能支持特定方向，适合进一步核查回传与业务端信息。',
'1010缺少事发SINR，容量函数无法计算，轨迹保留了该工具错误。其余有效指标仍能完成查询与对比，后端标出E3缺失并保留不确定性。这一测试可以区分两类现象：某个工具失败，以及整次调查无法取得必要证据。程序可以在明确保留缺口的情况下交付下一步核查建议。',
'模拟数据和规则使用了相近的专业假设，匹配率只能说明本次样例满足了预设判据。两例缺失变体相关，收集真实运营环境中的盲测结果需要额外授权和独立标签。当前十个案例每个配置只运行一次，因此暂时无法衡量不同模型环境、采样和重复运行的波动。',
'下一轮验证可以增加独立样本，按案例逐项核对单位、引用编号和实际建议，并记录阈值调整是否影响复合判断。关键取证结果和最终标签还可与工程师人工结论分别比对。')
add(PageBreak())

section('六、运行与复现')
paragraphs(
'提交包提供完整源代码、案例、Skill、测试、评测表和轨迹。运行依赖与模型服务的启动方式见README。先在终端启动支持工具调用的llama.cpp服务，再启动FastAPI。打开 /agent.html 可选择案例，或使用命令行指定案例与D配置并输出JSON。模型和服务程序按README另行配置。',
'运行 tests/evaluate_project.py 可重跑完整对照，默认输出到 results/reproduction，原实测结果保存在 results/final。复现时先检查模型端口和后端端口，再检查正常、缺失和复合案例。源代码测试包含早期规则原型和新增证据核对边界。',
'最终轨迹包含问题、实际工具参数、模型返回、用量以及核对结果。初版六例运行保留在 results 根目录，可用于对照开发过程。前端截图来自本地浏览器实际提交调查请求，报告中嵌入灰度版本。')
section('七、学习反思与小组分工')
paragraphs(
'这次最直接的收获是把调查结论拆回可核查的事实。模型负责理解问题、选择工具和组织解释，程序负责数据读取、单位明确的计算、证据核对和异常处理。从实际失败看，模型接到了正确工具回包也可能直接给出拥塞，需要把结论与对应证据留在同一份轨迹里。',
'后端工作涵盖模型服务接入、KPI工具、证据核对、后端接口与评测复现。前端工作涵盖案例选择、调查问题输入、工具回包、证据及建议的页面呈现。组员共同确定选题和前后端分工，并提供已有项目原型。Codex协助编写模型工具循环、证据核对、网页调查入口及评测脚本，并整理报告。核查过程包括对照工具回包检查误判、用缺失和复合案例测试核对逻辑，以及从ZIP解包后重跑代码测试、接口和完整评测。')
section('参考文献')
add(p('[1] C. E. Shannon. A Mathematical Theory of Communication. Bell System Technical Journal, 1948.',small))

doc=SimpleDocTemplate(str(root/'综合项目报告.pdf'),pagesize=A4,leftMargin=25*mm,rightMargin=25*mm,topMargin=23*mm,bottomMargin=23*mm,title='5G小区下行吞吐率异常调查Agent',author='5G Agent Project')
doc.build(S,onFirstPage=footer,onLaterPages=footer)
