import java.io.IOException;

public class CommandController {
    public boolean isReachable(String host) throws IOException, InterruptedException {
        Process process = new ProcessBuilder("sh", "-c", "ping -c 1 " + host).start();
        return process.waitFor() == 0;
    }
}
