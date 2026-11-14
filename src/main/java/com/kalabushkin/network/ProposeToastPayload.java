package com.kalabushkin.network;

import com.kalabushkin.Kalabushkin;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;

/** Sent by a client whose player proposes a toast with the words they typed. */
public record ProposeToastPayload(String text) implements CustomPayload {
	public static final int MAX_LENGTH = 100;
	public static final Id<ProposeToastPayload> ID = new Id<>(Kalabushkin.id("propose_toast"));
	public static final PacketCodec<RegistryByteBuf, ProposeToastPayload> CODEC =
			PacketCodecs.string(MAX_LENGTH).xmap(ProposeToastPayload::new, ProposeToastPayload::text).cast();

	@Override
	public Id<ProposeToastPayload> getId() {
		return ID;
	}
}
