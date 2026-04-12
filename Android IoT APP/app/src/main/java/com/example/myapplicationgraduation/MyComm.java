package com.example.myapplicationgraduation;

import com.alibaba.fastjson.JSONObject;

/**
 * IoT 网关通信协议格式化工具类。
 *
 * 所有 TCP 通信统一使用 JSON 格式，消息以换行符分隔。
 * 协议结构: {"op": "操作码", "data": <载荷>, "status": <状态码>}
 */
public class MyComm {

    /**
     * 构造命令 JSON 字符串。
     *
     * 旧格式 "op|data|status" 已替换为标准 JSON 格式。
     *
     * @param operation 操作码（如 "login", "light_th_open"）
     * @param data      载荷数据（字符串或 JSON 对象）
     * @param statusCode 状态码
     * @return JSON 字符串，如 {"op":"login","data":"...","status":"1"}
     */
    public String format_comm_data(String operation, String data, String statusCode) {
        JSONObject json = new JSONObject();
        json.put("op", operation);
        json.put("data", data);
        json.put("status", statusCode);
        return json.toJSONString();
    }
}
