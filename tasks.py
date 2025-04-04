from celery import Celery
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough, RunnableLambda
import json
from config import Config

celery = Celery('tasks', broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

llm = ChatOpenAI(base_url=Config.OPENAI_BASE_URL, api_key=Config.OPENAI_API_KEY, model=Config.OPENAI_MODEL)

@celery.task(bind=True)
def translate_task(self, text: str, target_lang: str) -> dict:
    """
    自动判断text文本语言，将这段文本翻译成target_lang目标语言 
    """
    print(f"任务:'{self.request.id}'开始运行...")
    str_output = StrOutputParser()
    # 1. 判断target_lang是否是有效语言类型
    target_lang_valid_prompt = PromptTemplate.from_template(
        """请验证以下输入语言名称是否为国家或民族语言。并直接返回该语言的中文名称。如果是无效语言名称或者跟语言类型没有关系，则返回"不支持"。
        输入语言: {target_lang}
        直接输出结果名称!!"""
    )
    target_lang_valid_chain = target_lang_valid_prompt | llm | str_output
    # 2. 文本语言检测
    source_lang_dect_prompt = PromptTemplate.from_template(
        """请判断以下文本所使用的语言，只需返回语言名称（如中文、英文、法语等）:
        文本: {text}"""
    )
    source_lang_dect_chain = source_lang_dect_prompt | llm | str_output
    # 3. 语言类型比较
    lang_compare_prompt = PromptTemplate.from_template(
        """请判断以下两种语言名称是否属于同一类型/语系:
        源语言: {source_lang}
        目标语言: {target_lang}
        只需返回'是'或者'否':"""
    )
    lang_compare_chain = lang_compare_prompt | llm | str_output
    # 4. 翻译成目标语言
    translate_prompt = PromptTemplate.from_template(
        """请将以下文本{source_lang}语言文本翻译成{target_lang}:
        文本: {text}
        直接输出翻译结果! """
    )
    translate_chain = translate_prompt | llm | str_output

    def printinfo(x):
        print("chain exec info", x)
        return x
    full_chain = (
        RunnableLambda(printinfo)
        # 验证target_lang是否有效
        | RunnablePassthrough.assign(target_lang=target_lang_valid_chain)
        | RunnableBranch(
            # target_lang无效，结束
            (lambda x: "不支持" in x["target_lang"], 
             lambda x: {"text": x["text"],"source_lang": "", "target_lang": x["target_lang"], "is_same_lang": "", "translated_text": ""}),
            # target_lang有效，翻译流程
            (RunnablePassthrough.assign(source_lang=source_lang_dect_chain) # 生成source_lang字段
             | RunnablePassthrough.assign(is_same_lang=lang_compare_chain) # 生成is_same_lang字段
             # 生成translated_text字段，如果is_same_lang为是，则直接使用text字段
             | RunnableBranch(
                (lambda x: "是" in x["is_same_lang"], lambda x: {"translated_text": x["text"]}),
                RunnablePassthrough.assign(translated_text=translate_chain)
            ))
        )
    )
    # full_chain.get_graph().print_ascii()
    result = full_chain.invoke({"text": text,"target_lang": target_lang})
    print(f"任务:'{self.request.id}'运行结束: {result}")
    return result

@celery.task(bind=True)
def summarize_task(self, text: str):
    """
    多维度总结text文本
    """
    print(f"任务:'{self.request.id}'开始运行...")
    summary_prompt = PromptTemplate.from_template("""
        请从以下文本中完成多维度分析，直接返回JSON格式结果，不要额外解释：

        文本内容：
        {text}

        分析要求：
        1. 关键点：提取3-5个关键点
        2. 情感基调：分析情感倾向(积极/中性/消极)及原因
        3. 总结：用一段话简洁总结主要内容
        4. 行动项：提取所有明确的行动项或待办事项

        返回格式：
        {{
            "key_points": ["点1", "点2", ...],
            "emotional_tone": {{"tone": "xx", "reason": "xx"}},
            "summary": "xx",
            "action_items": ["项1", "项2", ...]
        }}"""
    )
    chain = summary_prompt | llm | StrOutputParser() | RunnableLambda(json.loads)
    # chain.get_graph().print_ascii()
    result = chain.invoke({"text": text})
    print(f"任务:'{self.request.id}'运行结束: {result}")
    return result
