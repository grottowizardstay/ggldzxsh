package com.kalabushkin.client;

import com.kalabushkin.network.ProposeToastPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.gui.widget.TextFieldWidget;
import net.minecraft.screen.ScreenTexts;
import net.minecraft.text.Text;
import org.lwjgl.glfw.GLFW;

/** Asks the player for the words of their toast and sends them to the server. */
public class ToastScreen extends Screen {
	private static final int FIELD_WIDTH = 260;

	private TextFieldWidget words;

	public ToastScreen() {
		super(Text.translatable("screen.kalabushkin.toast.title"));
	}

	@Override
	protected void init() {
		int left = (width - FIELD_WIDTH) / 2;
		int top = height / 2 - 20;
		String typed = words == null ? "" : words.getText();
		words = new TextFieldWidget(textRenderer, left, top, FIELD_WIDTH, 20, title);
		words.setMaxLength(ProposeToastPayload.MAX_LENGTH);
		words.setPlaceholder(Text.translatable("screen.kalabushkin.toast.hint"));
		words.setText(typed);
		addDrawableChild(words);
		addDrawableChild(ButtonWidget.builder(Text.translatable("screen.kalabushkin.toast.propose"), button -> propose())
				.dimensions(left, top + 28, FIELD_WIDTH / 2 - 2, 20).build());
		addDrawableChild(ButtonWidget.builder(ScreenTexts.CANCEL, button -> close())
				.dimensions(left + FIELD_WIDTH / 2 + 2, top + 28, FIELD_WIDTH / 2 - 2, 20).build());
		setInitialFocus(words);
	}

	private void propose() {
		ClientPlayNetworking.send(new ProposeToastPayload(words.getText()));
		close();
	}

	@Override
	public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
		if (keyCode == GLFW.GLFW_KEY_ENTER || keyCode == GLFW.GLFW_KEY_KP_ENTER) {
			propose();
			return true;
		}
		return super.keyPressed(keyCode, scanCode, modifiers);
	}

	@Override
	public void render(DrawContext context, int mouseX, int mouseY, float delta) {
		super.render(context, mouseX, mouseY, delta);
		context.drawCenteredTextWithShadow(textRenderer, title, width / 2, height / 2 - 40, 0xFFFFFF);
	}

	@Override
	public boolean shouldPause() {
		return false;
	}
}
