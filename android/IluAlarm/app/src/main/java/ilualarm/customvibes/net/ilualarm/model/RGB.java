package ilualarm.customvibes.net.ilualarm.model;

import android.graphics.Color;

/**
 * Created by mariotti on 08/12/15.
 */
public class RGB {
    private int R;
    private int G;
    private int B;

    public RGB() {

    }

    public RGB(int r, int g, int b) {
        R = r;
        G = g;
        B = b;
    }

    public int getR() {
        return R;
    }

    public void setR(int r) {
        R = r;
    }

    public int getG() {
        return G;
    }

    public void setG(int g) {
        G = g;
    }

    public int getB() {
        return B;
    }

    public void setB(int b) {
        B = b;
    }

    public int getColor() {
        return Color.rgb(R, G, B);
    }
}
