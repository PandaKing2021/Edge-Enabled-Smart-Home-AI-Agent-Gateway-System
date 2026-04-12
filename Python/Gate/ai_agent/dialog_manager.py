"""对话管理器模块。

负责管理多轮对话上下文,维护会话历史。
"""

import json
import logging
import threading
import time
import uuid
from collections import deque
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DialogManager:
    """对话管理器,维护多轮对话上下文和历史记录。

    Attributes:
        max_context_turns: 最大保留对话轮数
        session_timeout: 会话超时时间(秒)
        sessions: 会话字典 {session_id: {"history": deque, "last_active": timestamp}}
    """

    def __init__(self, max_context_turns: int = 5, session_timeout: int = 3600) -> None:
        """初始化对话管理器。

        Args:
            max_context_turns: 最大保留对话轮数,默认5轮
            session_timeout: 会话超时时间(秒),默认1小时
        """
        self.max_context_turns = max_context_turns
        self.session_timeout = session_timeout
        self._lock = threading.Lock()
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, user_id: Optional[str] = None) -> str:
        """创建新会话。

        Args:
            user_id: 用户标识,可选

        Returns:
            session_id: 新会话ID
        """
        session_id = str(uuid.uuid4())
        with self._lock:
            self.sessions[session_id] = {
                "user_id": user_id,
                "history": deque(maxlen=self.max_context_turns),
                "last_active": time.time(),
            }
        logger.info("创建新会话: %s (用户: %s)", session_id, user_id)
        return session_id

    def add_message(
        self,
        session_id: str,
        user_input: str,
        agent_response: str,
        context_before: Optional[Dict] = None,
        context_after: Optional[Dict] = None,
    ) -> bool:
        """添加一轮对话到会话历史。

        Args:
            session_id: 会话ID
            user_input: 用户输入
            agent_response: Agent响应
            context_before: 执行前上下文,可选
            context_after: 执行后上下文,可选

        Returns:
            bool: 是否添加成功
        """
        with self._lock:
            if session_id not in self.sessions:
                logger.warning("会话不存在: %s", session_id)
                return False

            session = self.sessions[session_id]
            session["history"].append(
                {
                    "user_input": user_input,
                    "agent_response": agent_response,
                    "context_before": context_before,
                    "context_after": context_after,
                    "timestamp": time.time(),
                }
            )
            session["last_active"] = time.time()
            logger.debug("会话 %s 添加对话轮次: %s", session_id, user_input[:50])
            return True

    def get_context(self, session_id: str) -> List[Dict]:
        """获取会话上下文历史。

        Args:
            session_id: 会话ID

        Returns:
            List[Dict]: 对话历史列表
        """
        with self._lock:
            if session_id not in self.sessions:
                logger.warning("会话不存在: %s", session_id)
                return []

            session = self.sessions[session_id]
            return list(session["history"])

    def get_context_string(self, session_id: str) -> str:
        """获取会话上下文的字符串表示,用于LLM提示。

        Args:
            session_id: 会话ID

        Returns:
            str: 格式化的对话历史字符串
        """
        history = self.get_context(session_id)
        if not history:
            return "无历史对话"

        context_parts = []
        for i, turn in enumerate(history, 1):
            context_parts.append(f"第{i}轮:")
            context_parts.append(f"用户: {turn['user_input']}")
            context_parts.append(f"助手: {turn['agent_response']}")
            context_parts.append("")

        return "\n".join(context_parts)

    def clear_session(self, session_id: str) -> bool:
        """清空指定会话历史。

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否清空成功
        """
        with self._lock:
            if session_id not in self.sessions:
                return False

            self.sessions[session_id]["history"].clear()
            self.sessions[session_id]["last_active"] = time.time()
            logger.info("清空会话历史: %s", session_id)
            return True

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话。

        Returns:
            int: 清理的会话数量
        """
        current_time = time.time()
        expired_sessions = []

        with self._lock:
            for session_id, session in self.sessions.items():
                if current_time - session["last_active"] > self.session_timeout:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]

        if expired_sessions:
            logger.info("清理过期会话: %d个", len(expired_sessions))

        return len(expired_sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息。

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict]: 会话信息字典,不存在返回None
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                return {
                    "user_id": session["user_id"],
                    "last_active": session["last_active"],
                    "turn_count": len(session["history"]),
                }
            return None
