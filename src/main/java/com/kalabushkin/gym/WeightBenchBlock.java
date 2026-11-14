package com.kalabushkin.gym;

import java.util.EnumMap;
import java.util.Map;

import com.mojang.serialization.MapCodec;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.block.HorizontalFacingBlock;
import net.minecraft.block.ShapeContext;
import net.minecraft.block.enums.BedPart;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.state.StateManager;
import net.minecraft.state.property.EnumProperty;
import net.minecraft.state.property.Properties;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;
import net.minecraft.world.WorldAccess;

/**
 * A two-block bench with a barbell rack over its head half. FACING points from the foot half to
 * the head half, as on a bed. Use it with a barbell to lie down.
 */
public class WeightBenchBlock extends HorizontalFacingBlock {
	public static final MapCodec<WeightBenchBlock> CODEC = createCodec(WeightBenchBlock::new);
	public static final EnumProperty<BedPart> PART = Properties.BED_PART;
	/** Height of the pad surface, in blocks. */
	public static final double PAD_TOP = 10.0 / 16.0;

	private static final VoxelShape PAD = Block.createCuboidShape(0, 0, 0, 16, 10, 16);
	private static final Map<Direction, VoxelShape> HEAD_SHAPES = new EnumMap<>(Direction.class);

	static {
		for (Direction facing : Direction.Type.HORIZONTAL) {
			HEAD_SHAPES.put(facing, VoxelShapes.union(PAD,
					rotated(facing, 0.5, 3, 2.5, 5), rotated(facing, 13.5, 3, 15.5, 5)));
		}
	}

	public WeightBenchBlock(Settings settings) {
		super(settings);
		setDefaultState(getDefaultState().with(FACING, Direction.NORTH).with(PART, BedPart.FOOT));
	}

	/** A rack upright, given for a bench facing north and turned to {@code facing}. */
	private static VoxelShape rotated(Direction facing, double x1, double z1, double x2, double z2) {
		return switch (facing) {
			case SOUTH -> Block.createCuboidShape(16 - x2, 0, 16 - z2, 16 - x1, 16, 16 - z1);
			case EAST -> Block.createCuboidShape(16 - z2, 0, x1, 16 - z1, 16, x2);
			case WEST -> Block.createCuboidShape(z1, 0, 16 - x2, z2, 16, 16 - x1);
			default -> Block.createCuboidShape(x1, 0, z1, x2, 16, z2);
		};
	}

	private static Direction towardsOtherPart(BlockState state) {
		return state.get(PART) == BedPart.FOOT ? state.get(FACING) : state.get(FACING).getOpposite();
	}

	@Override
	protected MapCodec<? extends HorizontalFacingBlock> getCodec() {
		return CODEC;
	}

	@Override
	protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
		builder.add(FACING, PART);
	}

	@Override
	public BlockState getPlacementState(ItemPlacementContext ctx) {
		Direction facing = ctx.getHorizontalPlayerFacing();
		BlockPos head = ctx.getBlockPos().offset(facing);
		World world = ctx.getWorld();
		boolean fits = world.getBlockState(head).canReplace(ctx) && world.getWorldBorder().contains(head);
		return fits ? getDefaultState().with(FACING, facing) : null;
	}

	@Override
	public void onPlaced(World world, BlockPos pos, BlockState state, LivingEntity placer, ItemStack stack) {
		super.onPlaced(world, pos, state, placer, stack);
		if (!world.isClient) {
			world.setBlockState(pos.offset(state.get(FACING)), state.with(PART, BedPart.HEAD), Block.NOTIFY_ALL);
		}
	}

	@Override
	protected BlockState getStateForNeighborUpdate(BlockState state, Direction direction, BlockState neighborState,
			WorldAccess world, BlockPos pos, BlockPos neighborPos) {
		if (direction == towardsOtherPart(state)) {
			boolean whole = neighborState.isOf(this) && neighborState.get(PART) != state.get(PART);
			return whole ? state : Blocks.AIR.getDefaultState();
		}
		return super.getStateForNeighborUpdate(state, direction, neighborState, world, pos, neighborPos);
	}

	@Override
	public BlockState onBreak(World world, BlockPos pos, BlockState state, PlayerEntity player) {
		// The head half holds the drop; in creative it must go without dropping when the foot is broken.
		if (!world.isClient && player.isCreative() && state.get(PART) == BedPart.FOOT) {
			BlockPos head = pos.offset(state.get(FACING));
			if (world.getBlockState(head).isOf(this)) {
				world.setBlockState(head, Blocks.AIR.getDefaultState(), Block.NOTIFY_ALL | Block.SKIP_DROPS);
			}
		}
		return super.onBreak(world, pos, state, player);
	}

	@Override
	protected VoxelShape getOutlineShape(BlockState state, BlockView world, BlockPos pos, ShapeContext context) {
		return state.get(PART) == BedPart.HEAD ? HEAD_SHAPES.get(state.get(FACING)) : PAD;
	}

	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, BlockHitResult hit) {
		if (!(player instanceof ServerPlayerEntity serverPlayer)) {
			return ActionResult.SUCCESS;
		}
		if (BenchSeats.isLying(serverPlayer)) {
			Gym.benchRep(serverPlayer);
			return ActionResult.CONSUME;
		}
		if (!serverPlayer.getMainHandStack().isOf(GymContent.BARBELL)) {
			serverPlayer.sendMessage(Text.translatable("gym.kalabushkin.need_barbell"), true);
			return ActionResult.CONSUME;
		}
		Direction facing = state.get(FACING);
		BlockPos foot = state.get(PART) == BedPart.FOOT ? pos : pos.offset(facing.getOpposite());
		String message = BenchSeats.lieDown(serverPlayer, foot, facing)
				? "gym.kalabushkin.bench_hint" : "gym.kalabushkin.bench_taken";
		serverPlayer.sendMessage(Text.translatable(message), true);
		return ActionResult.CONSUME;
	}
}
