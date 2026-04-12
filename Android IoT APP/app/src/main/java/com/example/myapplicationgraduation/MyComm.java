package com.example.myapplicationgraduation;

import com.alibaba.fastjson.JSONObject;

/**
 * IoT gateway communication protocol formatting utility class.
 *
 * All TCP communication uses JSON format, messages are separated by newline.
 * Protocol structure: {"op": "operation code", "data": <payload>, "status": <status code>}
 */
public class MyComm {

    /**
     * Construct command JSON string.
     *
     * Old format "op|data|status" has been replaced with standard JSON format.
     *
     * @param operation Operation code (e.g., "login", "light_th_open")
     * @param data      Payload data (string or JSON object)
     * @param statusCode Status code
     * @return JSON string, e.g., {"op":"login","data":"...","status":"1"}
     */
    public String format_comm_data(String operation, String data, String statusCode) {
        JSONObject json = new JSONObject();
        json.put("op", operation);
        json.put("data", data);
        json.put("status", statusCode);
        return json.toJSONString();
    }
}
