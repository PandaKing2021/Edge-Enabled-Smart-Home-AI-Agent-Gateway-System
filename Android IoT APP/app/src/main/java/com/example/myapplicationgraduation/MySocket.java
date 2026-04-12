package com.example.myapplicationgraduation;

import java.io.BufferedInputStream;
import java.io.OutputStreamWriter;
import java.net.Socket;

public class MySocket extends Socket {
    private static String host;
    private static int port;
    private static OutputStreamWriter os;
    private static BufferedInputStream is;

    private static MySocket socket = null;

    private MySocket(String host, int port) throws Exception {
        super(host, port);
    }

    public static MySocket initSocket(String host, int port) throws Exception {
        MySocket.host = host;
        MySocket.port = port;
        socket = new MySocket(host, port);
        os = new OutputStreamWriter(socket.getOutputStream(), "UTF-8");
        is = new BufferedInputStream(socket.getInputStream());
        return socket;
    }

    public static MySocket getSocket() {
        return socket;
    }

    public static BufferedInputStream getIs() throws Exception {
        return is;
    }

    public static OutputStreamWriter getOs() throws Exception {
        return os;
    }

    /**
     * 发送一行文本（自动追加换行符作为消息分隔符）。
     *
     * @param info 要发送的文本消息（不应包含 \\n）
     */
    public static void sendInfo(String info) throws Exception {
        OutputStreamWriter tos = getOs();
        tos.write(info + "\n");
        tos.flush();
    }

    public static String getInfo() throws Exception {
        byte[] b = new byte[4096];
        BufferedInputStream tis = getIs();
        tis.read(b);
        String result = new String(b);
        return result.trim().substring(0, result.indexOf("\n"));
    }

}
